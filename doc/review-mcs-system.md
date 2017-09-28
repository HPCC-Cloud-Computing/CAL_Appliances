# Review MCS System

## Các vấn đề đã thực hiện được trong hệ thống MCS

Tổng hợp các nội dung trong đồ án của anh Kiên, các vấn đề đã thực hiện được trong MCS:

- Về giải pháp:

    1. Đã giải quyết được bài toán: Cho tên một Data Object, tìm các Cloud Server chứa các bản sao của Data Object đó bằng giải pháp: mô hình Cloud Chord Ring kết hợp Reference Node.
    1. Đã giải quyết bài toán độ trễ khi tạo mới một Data Object bằng giải pháp sử dụng Celery.
    1. Sử dụng pickle để lưu các ring của các user vào file và lưu trữ an toàn file này trên ổ cứng máy chủ.
- Về chức năng:
    1. Đã xây dựng được giao diện web cho hệ thống MCS.
    1. Đã xây dựng được các chức năng sau:
        - Đăng nhập
        - Đăng ký
        - Quản lý tập tin
        - Upload tập tin
        - Download tập tin
        - Xóa tập tin
        - Tạo thư mục
        - Quản lý, giám sát trạng thái của các đám mây của từng User
        - Cập nhật thông tin người dùng
        - Đăng xuất
        - Upload tập tin cấu hình

## Các vấn sẽ được giải quyết trong hệ thống MCOS

Tiếp tục phát triển hệ thống MCS, em xin đề xuất các vấn đề mà hệ thống MCOS sẽ giải quyết là:

- Triển khai MCOS trên môi trường scaling - multi processes
- Cho phép người dùng thêm, xóa Cloud trong danh sách các Cloud Server - Cloud Ring của người dùng.
- Sử dụng Swift Ring thay thế cho Chord Ring để tập trung vào tính chất Consistent Hashing của Ring, đồng thời tăng tốc độ lookup lên O(1).
- Xem xét việc tạm thời không implement cơ chế lưu trữ cây thư mục - folder để tập trung giải quyết bài toán tính nhất quán của dữ liệu.
- Xem xét vấn đề nhất quán dữ liệu trong MCOS trên cả 2 thành phần chính: Nhất quán dữ liệu giữa các bản sao của Ring trên các process và nhất quán dữ liệu giữa các bản sao của một Data Object.
- Xem xét lại việc có tiếp tục cung cấp hệ thống cho Multi User hay không, hay chỉ giới hạn hệ thống phục vụ cho một User, để hạn chế số lượng Ring/User có mặt trên hệ thống, nhằm tối ưu khả năng Scaling của hệ thống.

Cụ thể các vấn đề như sau:

### Bài toán thêm, xóa Cloud Server

Nội dung bài toán: Hệ thống Cloud Ring của người dùng đang có n cloud đang họat động, tại một thời điểm nào đó, người dùng muốn thêm vào Cloud Ring một số Cloud Server hoặc muốn gỡ bỏ một số Cloud Server khỏi Cloud Ring.

Yêu cầu của bài toán:

- Khi hệ thống đang xử lý tác vụ thêm mới, gỡ bỏ 1 số Cloud Server khỏi Cloud Ring, hệ thống vẫn phải đảm bảo các chức năng tương tác với các Data Object không bị gián đoạn, và sự ảnh hưởng của việc thực hiện tác vụ thêm mới/gỡ bỏ Cloud Ring tới hiệu năng của các thao tác liên quan tới Data Object là nhỏ nhất có thể.
- Trong trường hợp thêm mới Cloud Server, các bản sao của các Data Object phải được di chuyển hợp lý từ các Cloud Server cũ sang các Cloud Server mới, còn trong trường hợp gỡ bỏ Cloud Server, các bản sao của Data Object trên các Cloud Server chuẩn bị bị gỡ bỏ phải được di chuyển tới các Cloud Server còn lại trên hệ thống trước khi hệ thống thực hiện gỡ bỏ hoàn toàn các Cloud Server đó khỏi Cloud Ring của người dùng.
- Sau khi thực hiện xong tác vụ, Cloud Ring của người dùng trên tất cả các process phải có nội dung giống nhau.

Các vấn đề trong bài toán thêm, xóa Cloud Server:

- Khi thêm/xóa các Cloud Server trên một Cloud Ring, thì Cloud Ring sẽ bị thay đổi. Trong Swift Ring thì vị trí của một node là cố định nhưng khi thêm/xóa Cloud thì một số node sẽ thay đổi tham chiếu tới các Cloud Ring khác với các tham chiếu trước khi thêm/xóa cloud, dẫn tới việc vị trí của một số Data Object sẽ bị thay đổi. Vấn đề ở đây là: chúng ta cần biết được các Data Object nào cần được di chuyển, tức là chúng ta cần biết và quản lý được danh sách các DataObject có trên một Node.(Vấn đề tương tự cũng xuất hiện trong Swift => Swift xử lý vấn đề này như thế nào ?)

- Khi có nhiều yêu cầu thêm mới/xóa bỏ Cloud Server trên một Cloud Ring cùng một lúc, thì các thao tác này sẽ phải được thực thi lần lượt => Cần hàng đợi yêu cầu cho các request thêm mới/xóa bỏ cloud server.
- Làm sao để tối ưu việc cập nhật thay đổi Cloud Ring từ process xử lý yêu cầu tới các process khác trong hệ thống ?

Ví dụ về bài toán thêm, xóa Cloud Server:

### Bài toán đảm bảo tính nhất quán dữ liệu của các bản sao của một Data Object