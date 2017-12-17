#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
from datetime import datetime

from ops_report import common
from ops_report import config
# from ops_report import send_email
# from ops_report import generate_excel
# from ops_report import generate_excel_ceph
# from ops_report import nova_request
# from ops_report import zabbix_request
# from ops_report import cinder_request
# from ops_report import ceph_request

from flask_restful import Resource
from models.compute import ComputeModel
from models.compute import ZabbixClient
from models.compute import GenerateExcel


class Compute(Resource):
    def get(self):
        # For OpenStack
        user_admin = config.user_admin
        pass_admin = config.pass_admin
        keystone_ip = config.keystone_ip
        nova_ip = config.nova_ip
        nova_port = config.nova_port
        cinder_ip = config.cinder_ip
        cinder_port = config.cinder_port
        project_name = config.project_name
        project_id = config.project_id
        ratio_ram = config.ratio_ram
        ratio_cpu = config.ratio_cpu
        ssl = config.ssl

        # For Zabbix
        user_zabbix = config.user_zabbix
        pass_zabbix = config.pass_zabbix
        zabbix_ip = config.zabbix_ip
        zabbix_port = config.zabbix_port
        #
        # # For Ceph
        # ceph_ip = config.ceph_ip
        # ceph_port = config.ceph_port
        #


        token = common.get_token_v3(keystone_ip=keystone_ip, username=user_admin,
                                    password=pass_admin, project_name=project_name, ssl=ssl)
        nova_client = ComputeModel(token=token, nova_ip=nova_ip,
                                              port=nova_port, project_id=project_id, ssl=ssl)
        nova_hyper_list = nova_client.hyper_list_customize(ratio_ram=ratio_ram, ratio_cpu=ratio_cpu)
        zabbix_client = ZabbixClient(user_zabbix=user_zabbix,
                                             pass_zabbix=pass_zabbix,
                                             zabbix_ip=zabbix_ip,
                                             zabbix_port=zabbix_port)

        # Step 6:
        for name_compute, params in nova_hyper_list.items():
            try:
                compute_zabbix = config.mapping[name_compute]
                real_params = zabbix_client.get_param_host(compute_zabbix)
                nova_hyper_list[name_compute].update(real_params)
            except Exception as e:
                real_params = {'real_memory_used': 0, 'real_memory_mb': 0, 'percent_cpu': 0}
                nova_hyper_list[name_compute].update(real_params)

        return nova_hyper_list


class ComputeReport(Resource):
    # def gen_name_report_ops(self):
    #     path_dir = os.path.dirname(os.path.abspath(__file__))
    #     name_file = 'openstack_report_' + datetime.now().strftime(
    #         '%Y_%m_%d_%Hh_%M_%Ss') + '.xlsx'
    #     full_name_path = os.path.join(path_dir, name_file)
    #     return full_name_path

    def get(self):
        # For sending emails
        email_from = config.email_from
        pass_email_from = config.pass_email_from
        email_to = config.email_to.split(";")
        email_server = config.email_server

        nova_hyper_list = Compute().get()
        # Step 8: From nova_hyper_list, writing to excel file
 #       path_name_file_ops = self.gen_name_report_ops()
        path_dir = os.path.dirname(os.path.abspath(__file__))
        name_file = 'openstack_report_' + datetime.now().strftime(
            '%Y_%m_%d_%Hh_%M_%Ss') + '.xlsx'
        path_name_file_ops = os.path.join(path_dir, name_file)
        generate_excel = GenerateExcel()
        generate_excel.write_xls(file_name=path_name_file_ops, data=nova_hyper_list)
        # Step 10: After having this file, then it needs to send the file to Admin.
        generate_excel.send_mail(send_from=email_from, password=pass_email_from,
                             send_to=email_to, path_file_ops=path_name_file_ops,server=email_server)

        return {'message': 'Email was sent'}


