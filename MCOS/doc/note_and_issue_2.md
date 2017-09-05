# MCOS Note and Issue part 2

## Thiết kế đồng bộ vs thiết kế không đồng bộ

Có 2 phương án thiết kế hệ thống MCOS:

- Phương án 1: Không đồng bộ. Phương án này sẽ sử dụng Message queue cho một số tác vụ
- Phương án 2: Đồng bộ. Phương án này không sử dụng message queue mà các request từ cluster này sẽ được gửi trực tiếp sang cluster kia.

- Trong phương án không đồng bộ, thì khi hệ thống reply cho 1 số loại request của người dùng  thì sẽ chỉ thông báo là hệ thống đã tiếp nhận yêu cầu của người dùng, chứ không khẳng định khi người dùng nhận được reply thì nội dung của yêu cầu đã được thực thi hoàn toàn.
- Trong phương án đồng bộ, khi hệ thống reply cho người dùng, tức là yêu cầu của người dùng đã được hệ thống thực thi hoàn toàn thành công (hoặc thất bại).

Ví dụ: Khi hệ thống nhận được request **k** yêu cầu tạo một Data Object **x** mới:

- Với phương án không đồng bộ, hệ thống sẽ thực hiện một số các công việc như:
    - Xác định các Storage Service sẽ chứa Data Object **x**.
    - Chuyển tiếp công việc của request sang một service khác hoặc gửi vào 1 queue.
    - Reply cho người dùng Data Object đang được khởi tạo.
    
Khi người dùng nhận được Response cho request **k**, thì có nghĩa là Data Object **x** đang trong quá trình khởi tạo, State của Data Object **x** tại thời điểm hệ thống trả về response cho request **k** là CREATING.

- Với phương án đồng bộ, hệ thống sẽ phải thực hiện xong tất cả các công việc trong quá trình tạo Data Object **x**, sau đó mới được phép reply cho người dùng.

Trong phương án đồng bộ, khi người dùng nhận được Response cho request **k**, thì có nghĩa là Data Object **x** đã được tạo ra và cả 3 bản sao của **x** đã được thiết lập. State của Data Object **x** tại thời điểm hệ thống trả về response cho request **k** là CREATED.


Thiết kế của hệ thống:

Hệ thống bao gồm nhiều cụm (cluster) liên kết với nhau. Mỗi một Cluster bao gồm nhiều MCOS-Server Và MCOS-Resolver kết nối với một Backend Storage Service như Swift, Ceph, S3,...

Mỗi một Cluster được nhìn nhận như một Entrypoint duy nhất (một IP duy nhất đại diện cho Cluster.)

Hệ thống phục vụ nhiều người dùng cùng 1 lúc.

## Các API mà một Cluster cung cấp cho End User

```python
# 1. Đăng nhập
def login(user_name, password):
    pass

# 2. Liệt kê danh sách các container của User
def list_container():
    pass
    
# 3. Tạo Container mới:
def create_container(new_container_name):
    pass

# 4. Xem danh sách các Object chứa trong 1 container:
def list_object(container_name):
    pass

# 5. Xóa container:
def delete_container(container_name):
    pass

#6. Tạo mới Data Object
def create_object(container_name, object_name, content):
    pass
#7. Cập nhật Data Object
def update_object(container_name, object_name, updated_content):
    pass

#8. Xem thông tin Data Object
def stat_object(container_name, object_name):
    pass
#9. Download Data Object
def download_object(container_name, object_name):
    pass
#10. Xóa Data Object 
def delete_object(container_name, object_name):
    pass
```

## Phương án không đồng bộ - cách thức sử dụng message queue

