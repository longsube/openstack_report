
## Để cung cấp Ceph Rest API, cần phải khởi chạy server ceph-rest-api trên 1 host mon bất kỳ (VD sau thực hiện trên mon1)

- Lệnh để khởi chạy ceph-rest-api
```sh
#ceph-rest-api -c /etc/ceph/ceph.conf --cluster ceph -n client.admin
```

Lệnh trên sẽ khởi chạy rest api với:

- Sử dụng các cấu hình được khai báo trong /etc/ceph/ceph.conf
- Quyền cluster admin
- Khởi chạy cho cluster 'ceph'

- Tạo service /etc/init.d/ceph-rest-api để khởi chạy tự động

```sh
#! /bin/sh
# /etc/init.d/example

case "$1" in
  start)
    echo "Starting example"
    # run application you want to start
    /usr/bin/ceph-rest-api -c /etc/ceph/ceph.conf --cluster ceph -n client.admin &
    ;;
  stop)
    echo "Stopping example"
    # kill application you want to stop
    killall ceph-rest-api
    ;;
  restart)
   killall ceph-rest-api
   sleep 20
   /usr/bin/ceph-rest-api -c /etc/ceph/ceph.conf --cluster ceph -n client.admin
   ;;
  *)
    echo "Usage: /etc/init.d/example{start|stop}"
    exit 1
    ;;
esac

exit 0
```

- Khởi chạy service
```sh
/etc/init.d/ceph-rest-api start
```

- Cấu hình service tự động start khi boot
```sh
update-rc.d ceph-rest-api defaults
```

Tham khảo:

[1]- http://ceph.com/geen-categorie/experimenting-with-the-ceph-rest-api/

[2]- https://dmsimard.com/2014/01/01/documentation-for-ceph-rest-api/