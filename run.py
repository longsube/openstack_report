#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
from datetime import datetime

from ops_report import common
from ops_report import config
from ops_report import send_email
from ops_report import generate_excel
from ops_report import generate_excel_ceph
from ops_report import nova_request
from ops_report import zabbix_request
from ops_report import cinder_request
from ops_report import ceph_request


def gen_name_report_ops():
    path_dir = os.path.dirname(os.path.abspath(__file__))
    name_file = 'openstack_report_' + datetime.now().strftime(
        '%Y_%m_%d_%Hh_%M_%Ss') + '.xlsx'
    full_name_path = os.path.join(path_dir, name_file)
    return full_name_path

def gen_name_report_ceph():
    path_dir = os.path.dirname(os.path.abspath(__file__))
    name_file = 'ceph_report_' + datetime.now().strftime(
        '%Y_%m_%d_%Hh_%M_%Ss') + '.xlsx'
    full_name_path = os.path.join(path_dir, name_file)
    return full_name_path


def main():
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

    # For Ceph
    ceph_ip = config.ceph_ip
    ceph_port = config.ceph_port

    # For sending emails
    email_from = config.email_from
    pass_email_from = config.pass_email_from
    email_to = config.email_to.split(";")
    email_server = config.email_server

    # Step 1: Get token version 3
    token = common.get_token_v3(keystone_ip=keystone_ip, username=user_admin,
                                password=pass_admin, project_name=project_name, ssl=ssl)

    # Step 2: Get Hypervisors information from Nova
    nova_client = nova_request.NovaClient(token=token, nova_ip=nova_ip,
                                          port=nova_port,project_id=project_id, ssl=ssl)
    nova_hyper_list = nova_client.hyper_list_customize(ratio_ram=ratio_ram,
                                                       ratio_cpu=ratio_cpu)

    # Step 3: Get Cinder pool information from Cinder
    cinder_client = cinder_request.CinderClient(token=token, cinder_ip=cinder_ip,
                                                port=cinder_port, project_id=project_id, ssl=ssl)
    cinder_pools_list = cinder_client.pools_stats_detail()

    # Step 4: Get information from Ceph
    ceph_client = ceph_request.CephClient(ceph_ip=ceph_ip, ceph_port=ceph_port)

    ceph_pool_list = ceph_client.get_param_pool()

    # Step 5: Get information from Zabbix
    zabbix_client = zabbix_request.ZabbixClient(user_zabbix=user_zabbix,
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

    # Step 7:
    for pool_ceph, params in ceph_pool_list.items():
        try:
            pool_ops = list(config.mapping_ceph.keys())[list(config.mapping_ceph.values()).index(pool_ceph)]
            theory_params = cinder_pools_list[pool_ops]
            ceph_pool_list[pool_ceph].update(theory_params)
        except Exception as e:
            theory_params = {'total_gb': 0, 'used_gb': 0}
            ceph_pool_list[pool_ceph].update(theory_params)

    # Step 8: From nova_hyper_list, writing to excel file
    path_name_file_ops = gen_name_report_ops()
    generate_excel.write_xls(file_name=path_name_file_ops, data=nova_hyper_list)

    # Step 9: From cinder_pools_list, writing to excel file
    path_name_file_ceph = gen_name_report_ceph()
    generate_excel_ceph.write_xls(file_name=path_name_file_ceph, data=ceph_pool_list)

    # Step 10: After having this file, then it needs to send the file to Admin.
    send_email.send_mail(send_from=email_from, password=pass_email_from,
                    send_to=email_to, path_file_ops=path_name_file_ops,
                         path_file_ceph=path_name_file_ceph, server=email_server)

if __name__ == '__main__':
    main()
