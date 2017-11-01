# openstack_report
Script xuất báo cáo về tình trạng sử dụng tài nguyên trên lý thuyết và thực tế:
 - CPU và RAM lý thuyết đã cung cấp trên hệ thống OpenStack: sử dụng nova api.
 - CPU và RAM thực tế đã cung cấp trên các host compute: sử dụng Zabbix api (host compute đã cài đặt Zabbix agent và giám sát tập trung tại Zabbix Server)
 - Storage dành cho volume lý thuyết: sử dụng cinder-api (chưa lấy storage cho backup và image)
 - Storage dành cho volume thực tế: sử dụng ceph-api(tham khảo hướng dẫn cấu hình ở ![đây](ceph-rest-api.md))
