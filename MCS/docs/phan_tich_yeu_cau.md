# Phân tích yêu cầu của hệ thống

## 1. WSGI Server

Hệ thống được dự kiến xây dựng 2 giao diện: Command-line Interface và Web-based Interface.
Để tích hợp cả 2 giao diện này vào, chúng ta xây dựng một WSGI Server, 2 giao diện trên sẽ tương tác với WSGI Server thông qua RESTFul API.

Các ca sử dụng dưới đây được xây dựng dựa trên tiền đề là: Môi trường tương tác của người dùng là thông qua giao diện Web của hệ thống

### Use Case 1: Tạo tài khoản

Kịch bản: Người dùng truy cập vào giao diện tạo User mới trên trang Web

Input:
- Account_authentication:
    - Trường hợp 1: Google/Facebook/.. Authentication
    - Trường hợp 2: Account name/Password Authentication

- Email
- Initial Cloud List: Danh sách các cloud ban đầu mà người dùng có, tối thiểu là 1 cloud, thông tin về một cloud - Cloud Information:
    - Cloud Type (Swift, S3, Google Cloud, Ceph, ...)
    - Cloud Authentication. Ví dụ: với S3 cần có account_address, password/token; với Swift cần có IPAddress, account_address, pasword/token...

Output: Có 2 trường hợp:

- Trường hợp 1: Tạo thành công - thông báo kết quả ```is_created = True``` cho người dùng.
- Trường hợp 2: Tạo thất bại - thông báo ```is_created = False``` và báo lỗi đã xảy ra.

Processing:

- Xác thực tài khoản/ xác thực toàn bộ Cloud list
- Tạo 1 **AccountModel** dựa vào Input của khách hàng
- Lưu **AccountModel** trên vào ```Backend_Database```
- Khởi tạo các ID cho các Cloud trong Input Cloud list, tạo Cloud Ring.
- Khởi tạo **Root Folder** cho account mới tạo ra, replicate và lưu **Root Folder** này trên các cloud mà người dùng cung cấp trong Input.

### Use Case 2: Attach Cloud

Kịch bản: Một account muốn thêm cloud vào cloud_list

Input:

- Account_authentication:
- Clouds Information:
    - Cloud Type: Swift, S3, Google Cloud, Ceph, ...
    - Cloud Authentication: Account Name, IPAddress, Password/token

Output:

- Result

Processing:

- Kiểm tra thông tin xác thực của các Cloud mới.
- Lấy ra thông tin của account, Cloud Ring của account đó.
- Tạo ID cho Cloud mới, thêm node đại diện cho Cloud mới vào Ring.
- Di chuyển dữ liệu từ các cloud cũ sang cloud mới theo Chord Protocol.

### Use Case 3: Delete Cloud

Kịch bản: Người dùng muốn ngừng sử dụng một trong số các cloud của họ.

Input:

- Account authentication
- CloudID của cloud account muốn xóa

Output:

- Result
- Delete Status

Processing:

- Cập nhật Cloud Ring.
- Di chuyển dữ liệu từ cloud sắp bị loại bỏ sang các cloud khác.
- Xóa cloud bị loại bỏ ra khỏi hệ thống và thông báo kết quả cho người dùng.

### Use Case 4: View Account Information

Kịch bản: Người dùng muốn kiểm tra thông tin account.
Input:

- Account authentication

Output: Thông tin của Account - Danh sách các cloud. Mỗi cloud có những thông tin sau:

- Cloud Authentication
- Capacity
- Used Space
- Free Space
- Speed (Optional)
- Location (Optional)
- ...

Processing:

- Lấy thông tin về các cloud

### Use Case 5: Add Object/ File

Kịch bản: Người dùng thêm một Data Object

### Use Case 6: Get Object

### Use Case 7: Update Object

### Use Case 8 Delete Object


## 2. Deamon Process