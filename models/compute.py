# -*- coding: utf-8 -*-
from zabbix.api import ZabbixAPI
from ops_report import common
import json
import xlsxwriter
from email.mime import application
from email.mime import multipart
from email.mime import text as tx
from email.utils import formatdate
from os.path import basename
import smtplib


def get_zabbix(username, password, ip_zabbix, port):
    url = 'http://{0}:{1}/zabbix'.format(ip_zabbix, port)
    return ZabbixAPI(url=url, user=username, password=password)




class ComputeModel():
    def __init__(self, token, nova_ip=None, port=None, project_id=None, ssl=None):
        self.nova_ip = nova_ip
        self.port = port if port.upper() != 'NONE' else None
        self.token = token
        self.project_id = project_id
        self.ssl = ssl

    def hyper_list(self):
        if self.port is None:
            full_url_nova = '{0}://{1}/compute/v2.1/' \
                            '{2}/os-hypervisors/detail'.format(self.ssl, self.nova_ip, self.project_id)
        else:
            full_url_nova = '{0}://{1}:{2}/v2.1/' \
                            '{3}/os-hypervisors/detail'.format(self.ssl, self.nova_ip,
                                                               self.port, self.project_id)
        headers = {
            'X-Auth-Token': self.token,
            'Content-Type': 'application/json'
        }
        list_hyper = common.send_get_request(full_url_nova, headers=headers)
        result = list_hyper.result().content
     #   return result
    #    print(list_hyper)
        return json.loads(result)

    def hyper_list_customize(self, ratio_ram, ratio_cpu):
        """Get a list of hypervisor.
        :return: Output will be customized with Ram, CPU
        """
        list_hyper = self.hyper_list().get('hypervisors')
        output = {}
        for hypervisor in list_hyper:
            key_name_compute = hypervisor.get('hypervisor_hostname')
            output[key_name_compute] = {}
            output[key_name_compute].update({'memory_mb_used': hypervisor.get(
                'memory_mb_used')})
            output[key_name_compute].update({'memory_mb': (hypervisor.get(
                'memory_mb')) * float(ratio_ram)})
            output[key_name_compute].update({'vcpus_used': hypervisor.get(
                'vcpus_used')})
            output[key_name_compute].update({'vcpus': (hypervisor.get(
                'vcpus')) * float(ratio_cpu)})
        return output

class ZabbixClient():
    def __init__(self, user_zabbix, pass_zabbix, zabbix_ip, zabbix_port):
        self.username = user_zabbix
        self.password = pass_zabbix
        self.ip_zabbix = zabbix_ip
        self.zabbix_port = zabbix_port
        self.session = get_zabbix(self.username, self.password,
                                  self.ip_zabbix, self.zabbix_port)

    def get_param_host(self, hostname):

        #    output = {real_memory_used: 0, real_memory: 0, percent_CPU: 0}
        output = {}
        data = {
            "output": "extend",
            "host": hostname,
            "filter": {
                'key_': ["vm.memory.size[available]",
                         "vm.memory.size[total]",
                         "system.cpu.util[,system]"]
            },
            "sortfield": "name"
        }

        hosts = self.session.do_request(method='item.get', params=data)
        results = hosts.get('result')
        for result in results:
            if result.get('key_') == "vm.memory.size[available]":
                output['real_memory_used'] = common.byte_to_mb(int(result.get('lastvalue')))
            elif result.get('key_') == "vm.memory.size[total]":
                output['real_memory_mb'] = common.byte_to_mb(int(result.get('lastvalue')))
            elif result.get('key_') == "system.cpu.util[,system]":
                output['percent_cpu'] = float(result.get('lastvalue'))
            else:
                pass
        return output

class GenerateExcel():
    def __init__(self):
        pass

    def prepare_header(self, sheet, workbook):
        headers1 = ['Host', 'Ram', 'CPU']
        headers2 = ['Theory', 'Real', 'Theory']
        headers3 = ['Used (MB)', 'Total (MB)', 'Ratio (%)', 'Used (MB)', 'Total (MB)', 'Ratio (%)', 'Use (cores)', 'Total (cores)', 'Ratio (%)']
        header_format = workbook.add_format({
            'bold': 1,
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'fg_color': 'yellow'})
        sheet.merge_range('A4:K4', data='OpenStack Status', cell_format=header_format)
        sheet.merge_range('A6:A8', data=headers1[0], cell_format=header_format)
        sheet.merge_range('B6:G6', data=headers1[1], cell_format=header_format)
        sheet.merge_range('H6:K6', data=headers1[2], cell_format=header_format)
        col2 = 0
        for header2 in headers2:
            row2 = 6
            sheet.merge_range(row2, col2+1, row2, col2+3, header2,
                              cell_format=header_format)
            col2 = col2 + 3
        sheet.write(6, 10, 'Real', header_format)
        row3 = 7
        for col3, header3 in enumerate(headers3):
            col3 += 1
            sheet.write(row3, col3, header3, header_format)
        sheet.write(row3, 10, 'Percent CPU (%)', header_format)
        return sheet

    def write_xls(self,file_name, data):
        book = xlsxwriter.Workbook(file_name)
        format_col = book.add_format({'align': 'center', 'num_format': '0.0000'})
        sheet = book.add_worksheet('OpenStack_hypervisor')
        sheet.set_column('A:A', 20, cell_format=format_col)
        sheet.set_column('B:M', 15, cell_format=format_col)
        sheet.set_default_row(20, format_col)
        sheet = self.prepare_header(sheet,book)
        row = 8
        for name_com, params in data.items():
            sheet.write(row, 0, name_com)
            sheet.write_number(row, 1, params.get('memory_mb_used'))
            sheet.write_number(row, 2, params.get('memory_mb'))
            if params.get('memory_mb') != 0:
                ratio_ram_theory = (float(params.get('memory_mb_used'))/float(params.get('memory_mb')))*100
               # sheet.write_formula(row, 3, '=(B{0}/C{0})*100'.format(row+1))
                sheet.write_number(row, 3, ratio_ram_theory)
            else:
                sheet.write_formula(row, 3, '0')
            sheet.write_number(row, 4, params.get('real_memory_used'))
            sheet.write_number(row, 5, params.get('real_memory_mb'))
            if params.get('real_memory_mb') != 0:
                ratio_ram_real = (float(params.get('real_memory_used')) / float(params.get('real_memory_mb'))) * 100
                sheet.write_number(row, 6, ratio_ram_real)
             #   sheet.write_formula(row, 6, '=(E{0}/F{0})*100'.format(row+1))
            else:
                sheet.write_formula(row, 6, '0')
            sheet.write_number(row, 7, params.get('vcpus_used'))
            sheet.write_number(row, 8, params.get('vcpus'))
            if params.get('vcpus') != 0:
                ratio_cpu_theory = (float(params.get('vcpus_used')) / float(params.get('vcpus'))) * 100
                sheet.write_number(row, 9, ratio_cpu_theory)
              #  sheet.write_formula(row, 9, '=(H{0}/I{0})*100'.format(row+1))
            else:
                sheet.write_formula(row, 9, '0')
            sheet.write_number(row, 10, params.get('percent_cpu'))
            row += 1
        book.close()

    def send_mail(self,send_from=None, password=None, send_to=None,
                  path_file_ops=None, server=None):
        # Set default options
        subject = "Report OpenStack and Ceph status"
        text = "Dear Admin \n," \
               "I would like to send an email to report the status of Openstack and Ceph"

        hostname, port = server.split(':')
        msg = multipart.MIMEMultipart()
        msg['From'] = send_from
        msg['To'] = ', '.join(send_to)
        msg['Date'] = formatdate(localtime=True)
        msg['Subject'] = subject
        msg.attach(tx.MIMEText(text))
        with open(path_file_ops, "rb") as fil:
            part = application.MIMEApplication(fil.read(), Name=basename(path_file_ops))
            part['Content-Disposition'] = 'attachment; filename="%s"' % basename(path_file_ops)
            msg.attach(part)
        smtp = smtplib.SMTP(host=hostname, port=port)
        smtp.starttls()
        smtp.login(user=send_from, password=password)
        smtp.sendmail(send_from, send_to, msg.as_string())
        smtp.close()



