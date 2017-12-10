# For OpenStack
user_admin = 'admin'
pass_admin = 'xxxxxx'
keystone_ip = '172.16.69.50'
nova_ip = '172.16.69.50'
nova_port = '8774'
ratio_ram = '1.5'
ratio_cpu = '1.5'
project_name = 'admin'
project_id = 'xxxxx'
cinder_ip = '172.16.69.50'
cinder_port = '8776'
ssl = 'https'

# For Zabbix
user_zabbix = 'Admin'
pass_zabbix = 'zabbix'
zabbix_ip = '172.16.69.45'
zabbix_port = '80'

# For Ceph
ceph_ip = '172.16.69.167'
ceph_port = '5000'

# For sending emails
email_from = 'abc@email.com'
pass_email_from = 'xxx'
email_to = 'xxxx@gmail.com; yyy@email.com'
email_server = 'xxxxx:port'

# Mapping Nova with Zabbix
mapping = {
    'compute1.hn.vnpt': 'com1_hn',
    'compute2.hn.vnpt': 'com2_hn',
}

# Mapping storage pool between OpenStack and Ceph
mapping_ceph = {
    'ceph_hdd': 'volumes-hdd',
