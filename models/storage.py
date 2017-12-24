# -*- coding: utf-8 -*-
from ops_report import common
import json
import xlsxwriter
from email.mime import application
from email.mime import multipart
from email.mime import text as tx
from email.utils import formatdate
from os.path import basename
import smtplib

class StorageModel:
    def __init__(self, token, cinder_ip=None, port=None, project_id=None, ssl=None):
        self.cinder_ip = cinder_ip
        self.port = port if port.upper() != 'NONE' else None
        self.token = token
        self.project_id = project_id
        self.ssl = ssl

    def pools_stats(self):
        if self.port is None:
            full_url_cinder = '{0}://{1}/v2/' \
                            '{2}/scheduler-stats/get_pools?detail=True'.format(self.ssl,self.cinder_ip,self.project_id)
        else:
            full_url_cinder = '{0}://{1}:{2}/v2/' \
                            '{3}/scheduler-stats/get_pools?detail=True'.format(self.ssl,self.cinder_ip,
                                                           self.port,self.project_id)
        headers = {
            'X-Auth-Token': self.token,
            'Content-Type': 'application/json'
        }
        stats_pools = common.send_get_request(full_url_cinder, headers=headers)
        result = stats_pools.result().json()
        return result


    def pools_stats_detail(self):
        """Get a list of pool.
        :return: Output is Total capacity and used capacity in GB
        """
        list_pools = self.pools_stats().get('pools')
       # print(list_pools)
        output = {}
        for pool in list_pools:
            key_name_pool = pool.get('capabilities').get('volume_backend_name')
            output[key_name_pool] = {}
            output[key_name_pool].update({'total_gb': pool.get('capabilities').get(
                'total_capacity_gb')})
            output[key_name_pool].update({'used_gb': (pool.get('capabilities').get(
                'total_capacity_gb')) - (pool.get('capabilities').get(
                'free_capacity_gb'))})
        return output

class CephModel():

    def __init__(self, ceph_ip, ceph_port):
        self.ceph_ip = ceph_ip
        self.ceph_port = ceph_port


    def get_param_pool(self):
        full_url = 'http://{0}:{1}/api/v0.1/df?detail'.format(self.ceph_ip, self.ceph_port)
        headers = {'Accept': 'application/json'}
        status = common.send_get_request(full_url, headers=headers)
        result = status.result().json()
        pools = result.get('output').get('pools')

        output = {}
        for pool in pools:
            keyname_pool = pool.get('name')
            output[keyname_pool] = {}
            mbytes_used = common.byte_to_gb(pool.get('stats').get('bytes_used'))
            mbytes_avail = common.byte_to_gb(pool.get('stats').get('max_avail'))
            mbytes_total = mbytes_used + mbytes_avail
            output[keyname_pool].update({'real_used_gb': mbytes_used})
            output[keyname_pool].update({'real_total_gb': mbytes_total})
        return output

class GenerateExcel():
    def __init__(self):
        pass

    def prepare_header(self, sheet, workbook):
        headers1 = ['Pool', 'Storage']
        headers2 = ['Theory', 'Real']
        headers3 = ['Used (GB)', 'Total (GB)', 'Ratio (%)'] * 2
        header_format = workbook.add_format({
            'bold': 1,
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'fg_color': 'yellow'})
        sheet.merge_range('A4:G4', data='Ceph Status', cell_format=header_format)
        sheet.merge_range('A6:A8', data=headers1[0], cell_format=header_format)
        sheet.merge_range('B6:G6', data=headers1[1], cell_format=header_format)
        col2 = 0
        for header2 in headers2:
            row2 = 6
            sheet.merge_range(row2, col2 + 1, row2, col2 + 3, header2,
                              cell_format=header_format)
            col2 = col2 + 3
        row3 = 7
        for col3, header3 in enumerate(headers3):
            col3 += 1
            sheet.write(row3, col3, header3, header_format)
        return sheet

    def write_xls(self,file_name, data):
        book = xlsxwriter.Workbook(file_name)
        format_col = book.add_format({'align': 'center', 'num_format': '0.0000'})
        sheet = book.add_worksheet('Storage_Usage')
        sheet.set_column('A:A', 20, cell_format=format_col)
        sheet.set_column('B:M', 15, cell_format=format_col)
        sheet.set_default_row(20, format_col)
        sheet = self.prepare_header(sheet, book)
        row = 8
        for name_com, params in data.items():
            sheet.write(row, 0, name_com)
            sheet.write_number(row, 1, params.get('used_gb'))
            sheet.write_number(row, 2, params.get('total_gb'))
            if params.get('total_gb') != 0:
                ratio_storage_theory = (float(params.get('used_gb')) / float(params.get('total_gb'))) * 100
                sheet.write_number(row, 3, ratio_storage_theory)
                #     sheet.write_formula(row, 3, '=(B{0}/C{0})*100'.format(row+1))
            else:
                sheet.write_formula(row, 3, '0')
            sheet.write_number(row, 4, params.get('real_used_gb'))
            sheet.write_number(row, 5, params.get('real_total_gb'))
            if params.get('real_total_gb') != 0:
                ratio_storage_real = (float(params.get('real_used_gb')) / float(params.get('real_total_gb'))) * 100
                sheet.write_number(row, 6, ratio_storage_real)
                # sheet.write_formula(row, 6, '=(E{0}/F{0})*100'.format(row+1))
            else:
                sheet.write_formula(row, 6, '0')
            row += 1
        book.close()

    def send_mail(self,send_from=None, password=None, send_to=None,
                  path_file_ceph=None, server=None):
        # Set default options
        subject = "Report Ceph status"
        text = "Dear Admin \n," \
               "I would like to send an email to report the status of Ceph"

        hostname, port = server.split(':')
        msg = multipart.MIMEMultipart()
        msg['From'] = send_from
        msg['To'] = ', '.join(send_to)
        msg['Date'] = formatdate(localtime=True)
        msg['Subject'] = subject
        msg.attach(tx.MIMEText(text))
        with open(path_file_ceph, "rb") as fil:
            part = application.MIMEApplication(fil.read(), Name=basename(path_file_ceph))
            part['Content-Disposition'] = 'attachment; filename="%s"' % basename(path_file_ceph)
            msg.attach(part)
        smtp = smtplib.SMTP(host=hostname, port=port)
        smtp.starttls()
        smtp.login(user=send_from, password=password)
        smtp.sendmail(send_from, send_to, msg.as_string())
        smtp.close()


