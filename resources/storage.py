#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
from datetime import datetime

from ops_report import common
from ops_report import config

from flask_restful import Resource
from models.storage import StorageModel
from models.storage import CephModel
from models.storage import GenerateExcel

class Storage(Resource):
    def get(self):
        user_admin = config.user_admin
        pass_admin = config.pass_admin
        keystone_ip = config.keystone_ip
        project_name = config.project_name
        project_id = config.project_id
        ssl = config.ssl
        cinder_ip = config.cinder_ip
        cinder_port = config.cinder_port

        # For Ceph
        ceph_ip = config.ceph_ip
        ceph_port = config.ceph_port

        token = common.get_token_v3(keystone_ip=keystone_ip, username=user_admin,
                                    password=pass_admin, project_name=project_name, ssl=ssl)

        # Step 3: Get Cinder pool information from Cinder
        cinder_client = StorageModel(token=token, cinder_ip=cinder_ip,
                                                    port=cinder_port, project_id=project_id, ssl=ssl)
        cinder_pools_list = cinder_client.pools_stats_detail()

        # Step 4: Get information from Ceph
        ceph_client = CephModel(ceph_ip=ceph_ip, ceph_port=ceph_port)

        ceph_pool_list = ceph_client.get_param_pool()

        # Step 7:
        for pool_ceph, params in ceph_pool_list.items():
            try:
                pool_ops = list(config.mapping_ceph.keys())[list(config.mapping_ceph.values()).index(pool_ceph)]
                theory_params = cinder_pools_list[pool_ops]
                ceph_pool_list[pool_ceph].update(theory_params)
            except Exception as e:
                theory_params = {'total_gb': 0, 'used_gb': 0}
                ceph_pool_list[pool_ceph].update(theory_params)
        return ceph_pool_list

class StorageReport(Resource):
    def get(self):
        email_from = config.email_from
        pass_email_from = config.pass_email_from
        email_to = config.email_to.split(";")
        email_server = config.email_server

        ceph_pool_list = Storage().get()

        path_dir = os.path.dirname(os.path.abspath(__file__))
        name_file = 'ceph_report_' + datetime.now().strftime(
            '%Y_%m_%d_%Hh_%M_%Ss') + '.xlsx'
        path_name_file_ceph = os.path.join(path_dir, name_file)
        generate_excel_ceph = GenerateExcel()
        generate_excel_ceph.write_xls(file_name=path_name_file_ceph, data=ceph_pool_list)

        # Step 10: After having this file, then it needs to send the file to Admin.
        generate_excel_ceph.send_mail(send_from=email_from, password=pass_email_from,
                             send_to=email_to, path_file_ceph=path_name_file_ceph, server=email_server)

        return {'message': 'Email was sent'}