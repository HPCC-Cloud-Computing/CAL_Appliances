# Review việc thực hiện đồ án

## 1.Mục tiêu của đồ án

Đồ án MCOS có 2 mục tiêu chính là:

- Triển khai phân tán hệ thống multi object-storage dưới dạng một tập hợp các cluster kết nối với nhau theo mô hình ngang hàng peer-to-peer.
- Implement mô hình multi-option khi lưu trữ data-object.

## 2. Các công việc đã thực hiện được

Cho tới thời điểm hiện tại, các công việc đã thực hiện được là:

- Xây dựng xong thiết kế tổng quan của hệ thống
- Xây dựng xong một số chức năng chính của hệ thống:
    - Thiết lập kết nối giữa các cluster với nhau trong quá trình khởi tạo hệ thống.
    - Thiết lập cơ chế kiểm tra trạng thái của các cluster thông qua message queue.
    - Thiết lập cơ chế xác thực và phân quyền sử dụng keystone
    - Cơ chế tạo account ring, container ring và phân phối ring
    - Xây dựng về cơ bản giao diện của admin và user.
- Đã thử nghiệm benchmark cloud với hệ số replica = 1

## 3. Các công việc dự kiến hoàn thành trong thời gian còn lại của đồ án

- Thử nghiệm benchmark cloud với hệ số = 2,3
- Thử nghiệm benchmark cloud với loại ổ đĩa là SSD (ảo hóa bằng RAM).
- Xây dựng cơ chế tạo các ring trong multi-ring
- Implement các cơ chế phục vụ user: Tạo container, tạo file, xóa file...