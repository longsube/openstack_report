# openstack_report
Script xuất báo cáo về tình trạng sử dụng tài nguyên trên lý thuyết và thực tế:
 - CPU và RAM lý thuyết đã cung cấp trên hệ thống OpenStack: sử dụng nova api.
 - CPU và RAM thực tế đã cung cấp trên các host compute: sử dụng Zabbix api (host compute đã cài đặt Zabbix agent và giám sát tập trung tại Zabbix Server)
 - Storage dành cho volume lý thuyết: sử dụng cinder-api (chưa lấy storage cho backup và image)
 - Storage dành cho volume thực tế: sử dụng ceph-api(tham khảo hướng dẫn cấu hình ở ![đây](ceph-rest-api.md))
 - Phiên bản OpenStack tương thích: Mitaka
 - Phiên bản Ceph tương thích: Jewel
 - Phiên bản Zabbix tương thích: 3.0
 - Phiên bản Python: 2.7.5 hoặc 3.5.6

Script này chạy trên 1 máy Client (172.16.69.81), có khả năng kết nối tới các API của OpenStack, Zabbix Server, Ceph để thu thập các thông tin báo cáo.


# Hướng dẫn sử dụng


## 1.Cài đặt Apache2
  - Cài đặt gói
  	```sh
  	apt-get install apache2 -y
  	```
  - Cài đặt gói mod-proxy-uwsgi cho apache
	```sh
	apt-get install -y libapache2-mod-proxy-uwsgi
	a2enmod proxy
	a2enmod proxy_uwsgi
	service apache2 restart
	```

  - Tạo file cấu hình /etc/apache2/sites-available/report.conf
	```sh
	Listen 0.0.0.0:80
	# Option để apache2 giao tiếp với uwsgi thông qua socket (chú ý từ apache 2.4.9 trở lên mới hỗ trợ)
	ProxyPass / unix:/var/www/html/openstack_report/socket.sock|uwsgi://127.0.0.1:5000/
	# Option để apache2 giao tiếp với uwsgi thông qua http
	ProxyPass / uwsgi://127.0.0.1:5000/
	```

  - Xóa file cấu hình mặc định để tránh trùng port 80 (nếu ko xóa thì chuyển sang dùng port khác)
    ```sh
    rm /etc/apache2/sites-enabled/000-default.conf
    ```

  - Tạo soft link cho file cấu hình vừa tạo 
	```sh
	ln -s /etc/apache2/sites-available/report.conf /etc/apache2/sites-enabled/report.conf
	service apache2 restart
	```
  - Nếu muốn giao tiếp với uwsgi qua socket, cần phải upgrade phiên bản apache2 lên mới nhất (> 2.4.9)
  	```sh
  	add-apt-repository ppa:ondrej/apache2
	apt-get update
	apt-get install --only-upgrade apache2
  	```

## 3. Tải chương trình
  - Cài đặt git
  	```sh
  	apt-get update
  	apt-get install git -y
  	```
  - Clone chương trình
  	```sh
  	git clone -b longlq_v2 https://github.com/longsube/openstack_report.git
  	mkdir /var/www/html/openstack_report
  	cp /root/openstack_report/* /var/www/html/openstack_report
  	```

  - Cài đặt python 3.6
  	```sh
  	sudo add-apt-repository ppa:jonathonf/python-3.6
	sudo apt-get update
	sudo apt-get install python3.6
  	```

  - Cài đặt virtualenv
  	```sh
  	pip install virtualenv
  	```

  - Tạo virtual enviroment
  	```sh
  	cd /var/www/html/openstack_report
  	virtualenv venv -p python3.6
  	source venv/bin/activate
  	```

  - Cài đặt python3.6 dev
  	```sh
  	apt-get install python3.6-dev -y
  	```
  	
  - Cài đặt các package yêu cầu
  	```sh
  	cd /var/www/html/openstack_report
  	pip install -r requirement.txt
  	```
  - Thay đổi các thông số cấu hình trong /root/openstack_report/ops_report/config.py
	```sh
	# For OpenStack (khai báo các thông số cấu hình để kết nối tới OpenStack)
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

	# For Zabbix (khai báo các thông số cấu hình để kết nối tới Zabbix)
	user_zabbix = 'Admin'
	pass_zabbix = 'zabbix'
	zabbix_ip = '172.16.69.45'
	zabbix_port = '80'

	# For Ceph (khai báo các thông số cấu hình để kết nối tới Ceph)
	ceph_ip = '172.16.69.167'
	ceph_port = '5000'

	# For sending emails (khai báo mail sử dụng để gửi và nhận các báo cáo thống kê, ngăn cách bằng dấu ;)
	email_from = 'abc@email.com'
	pass_email_from = 'xxx'
	email_to = 'xxxx@gmail.com; yyy@email.com'
	email_server = 'xxxxx:port'

	# Mapping Nova with Zabbix (compute1.hn.vnpt: tên compute trên OpenStack, com1_hn: tên compute trêm Zabbix)
	mapping = {
	    'compute1.hn.vnpt': 'com1_hn',
	    'compute2.hn.vnpt': 'com2_hn',
	}

	# Mapping storage pool between OpenStack and Ceph (ceph_hdd: tên pool storage trên OpenStack, volumes_hdd: tên pool volume trên Ceph)
	mapping_ceph = {
	    'ceph_hdd': 'volumes-hdd',
	}
	```

  - Tạo thư mục chứa file log
  	```sh
  	mkdir /var/www/html/openstack_report/log
  	```

  - Sửa file /var/www/html/openstack_report/uwsgi.ini
	```sh 
	[uwsgi]
	base = /var/www/html/openstack_report
	app = run
	module = %(app)
	home = %(base)/venv
	pythonpath = %(base)
	# Giao tiếp với apache2 qua unix socket
	socket = %(base)/socket.sock
	# Giao tiếp với Apache2 qua http
	socket = 127.0.0.1:5000
	chmod-socket =777
	processes = 8
	threads = 8
	harakiri = 15
	callable = app
	logto = /var/www/html/openstack_report/log/%n.log
	```

  - Tạo file service cho uwsgi `/etc/init/uwsgi.conf` (Ubuntu14.04 dùng Upstart (init))
  	```sh
	description "uWSGI items rest"
	start on runlevel [2345]
	stop on runlevel [!2345]
	respawn
	exec /var/www/html/openstack_report/venv/bin/uwsgi --master --emperor /var/www/html/openstack_report/uwsgi.ini --die-on-term --uid root --gid root --logto /var/www/html/openstack_report/emperor.log
	```

  - Khởi động uwsgi service
  	```sh
	service uwsgi start
	```
  - Kiểm tra log service uwsgi
  	```sh
  	tailf /var/www/html/openstack_report/log/uwsgi.log
  	```
  	Kết quả:
  	```sh
  	*** Operational MODE: preforking+threaded ***
	added /var/www/html/openstack_report/ to pythonpath.
	WSGI app 0 (mountpoint='') ready in 1 seconds on interpreter 0x1a9fbc0 pid: 21232 (default app)
	*** uWSGI is running in multiple interpreter mode ***
	spawned uWSGI master process (pid: 21232)
	spawned uWSGI worker 1 (pid: 21236, cores: 8)
	spawned uWSGI worker 2 (pid: 21237, cores: 8)
	spawned uWSGI worker 3 (pid: 21238, cores: 8)
	spawned uWSGI worker 4 (pid: 21239, cores: 8)
	spawned uWSGI worker 5 (pid: 21240, cores: 8)
	spawned uWSGI worker 6 (pid: 21241, cores: 8)
	spawned uWSGI worker 7 (pid: 21242, cores: 8)
	spawned uWSGI worker 8 (pid: 21243, cores: 8)
	```

## 4. Thử nghiệm API
  - Dùng curl gọi 1 GET request tới API
	```sh
	curl http://127.0.0.1:80/compute
	```
  - Kết quả nhận được một dict dữ liệu rỗng:
	```sh
	{"compute2.hn.vnpt": {"memory_mb_used": 1024, "memory_mb": 5928.0, "vcpus_used": 1, "vcpus": 6.0, "real_memory_used": 3077.30078125, "percent_cpu": 2.1479, "real_memory_mb": 3952.359375}, "compute1.hn.vnpt": {"memory_mb_used": 512, "memory_mb": 5928.0, "vcpus_used": 0, "vcpus": 6.0, "real_memory_used": 3269.98046875, "percent_cpu": 1.3246, "real_memory_mb": 3952.359375}, "compute3.hn.vnpt": {"memory_mb_used": 512, "memory_mb": 5928.0, "vcpus_used": 0, "vcpus": 6.0, "real_memory_used": 0, "real_memory_mb": 0, "percent_cpu": 0}, "compute4.hn.vnpt": {"memory_mb_used": 512, "memory_mb": 5928.0, "vcpus_used": 0, "vcpus": 6.0, "real_memory_used": 0, "real_memory_mb": 0, "percent_cpu": 0}, "localhost.localdomain": {"memory_mb_used": 512, "memory_mb": 5928.0, "vcpus_used": 0, "vcpus": 6.0, "real_memory_used": 0, "real_memory_mb": 0, "percent_cpu": 0}}
	```

## 5. Mail báo cáo được gửi về mail, có dạng như sau:

![mail_1](images/mail_1.jpg)

![mail_2](images/mail_2.jpg)

![mail_3](images/mail_3.jpg)






