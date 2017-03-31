# Những vấn đề còn gặp phải.

1. Làm sao định kỳ thực hiện health check các CloudServer trong CloudRing.
   Giải pháp khả thi:
    - Thực hiện ping đến CloudServer.
    - Thực hiện gửi bản tin đến địa chỉ ip và port đã định sẵn. Với swift có
      thể sử dụng port default (hoặc cho ng dùng cấu hình). S3?
    - Thực hiện check qua API?

2. Trường hợp tất cả replica nằm trên cùng 1 CloudServer. Làm sao để loại bỏ
   trường hợp đấy? (Nếu chỉ một số trong các replica nằm cùng trên CloudServer
   thì ok).
   Đơn giản: Khi PUT replica xuống CloudServer A thực hiện check xem có replica
   nào của DataObject đó có ở CloudServer A chưa? Nếu có trùng lặp, hash lại
   id và lặp lại từ đầu, kiểm tra và PUT.

3. Cache queue và single thread -> bottleneck.

4. Trong trường hợp, DataObject vẫn trong hàng đợi, đẩy bản cập nhật 01 xuống
   tất cả các replica (Tức không phải tất cả replica.is\_updated = True), thì
   User tiếp tục thực hiện cập nhật với  bản cập nhật 02. Lựa chọn:
   - Giữ nguyên cả 2 bản cập nhật. (Đối với bản cập nhật 02, tạo mới replica)
     và thông báo lại cho người dùng.

5. Vấn đề Join/Leave CloudServer trong CloudRing. Khi join/leave, thì cần cập
   nhật lại vị trí các replica nằm sai vị trí. Những vấn đề xảy ra:
   - Cập nhật như thế nào? Di chuyển như thế nào?
   - Trong thời gian di chuyển, những replica cần được di chuyển đánh dấu là
     updated = False và DataObject vẫn sẽ trong trạng thái chưa đồng bộ
     xong. Tuy nhiên, khi đang cập nhật như vậy, có request đến DataObject
     đó. Và các replica đều đang cập nhật. --> Thông báo ng dùng chờ? [bad
     idea].
   - Khi 1 CloudServer leave CloudRing, replica.is\_updated = False và điều
     hướng sang các replica.is\_updated = True. Tuy nhiên, sẽ có trường hợp
     nhiều hơn một CloudServer leave, và có thể tất cả các replica của
     DataObject đều nằm trên những CloudServer bị loại bỏ đó. Quay lại bài
     toán di chuyển phía trên.
6. Gán constraint cho thời gian định kỳ check. (có gán giá trị default và cho
   User thay đổi, nhưng chỉ được thay đổi trong khoảng cho trước).
7. Xử lý khi có một CloudServer gặp lỗi (quay lại bài toán health check phía
   trên).

8. Vấn đề xảy ra khi User add thêm một Cloud Node vào hệ thống. Nếu như trong Cloud Node mới đã có sẵn các Data Object ==> Có thêm luôn các Data Object đó vào hệ thống hay không ?

9. Vấn đề về User Account:

Đề xuất: Sử dụng mô hình của OpenStack:

Hệ thống sẽ có một Admin, Admin có quyền tạo ra Project và User, đồng thời có quyền thiết lập một User được dùng Project nào trong hệ thống.

Admin có quyền thiết lập User có quyền Admin đối với một Project trong hệ thống. Admin của một Project có quyền thêm / xóa các Cloud Node của Project đó