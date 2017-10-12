# Proposal Solution For Create And Distributed Ring Problem In MCOS System

Trong quá trình xây dựng hệ thống MCOS, một vấn đề xuất hiện cần phải giải quyết là: Làm sao để thực hiện thao tác tạo Ring và phân phối Ring được tạo ra tới các Cluster trong hệ thống MCOS, trong điều kiện trạng thái của hệ thống không ổn định mà thay đổi liên tục. Mô tả chi tiết về vấn đề được phát biểu như sau:

Tại thời điểm t, người quản trị hệ thống gửi request lên một trong các Cluster trên hệ thống yêu cầu hệ thống tạo Ring. Tại thời điểm này,đối với với Cluster nhận request, đang có **x** Cluste, và trong **x** Cluster này có **x1** Cluster đang ở trạng thái Active, và **x2** Cluster đang ở trạng thái InActive. Tại thời điểm **t + delta\_t** sẽ có thêm một cluster kết nối vào hệ thống. Tại thời điểm **t +delta\_t\_i** một Cluster trong số các Cluster đang Inactive sẽ kết nối trở lại hệ thống. 

Vấn đề cần giải quyết ở đây là làm sao để Các Cluster Inactive sau khi kết nối trở lại hệ thống, cũng như các Cluster mới kết nối tới hệ thống nhận được Ring được tạo ra tại thời điểm **t**. Một vấn đề khác đi cùng vấn đề này, đó là khi một Ring nào đó được cập nhật, chúng ta cũng cần phải gửi Ring mới tới các Cluster trên hệ thống.

Giải pháp mà em đề xuất là: Sau khi Ring được tạo ra ở Cluster nhận Request, Cluster này sẽ gửi Ring lên message queue kèm với 3 thông tin định danh là

- ring_name
- version 
- timeStamp 

và **Routing\_key** là "ring". Tất cả các Cluster trên hệ thống sẽ đều có một queue để listen **Routing\_key** này. 

Đồng thời, định kỳ một khoảng thời gian delta\_t, các Cluster trên hệ thống sẽ gửi message chứa các Ring tới message_queue với **Routing\_key** này.

Redis\_server trên cluster khi nhận được message chứa Ring sẽ kiểm tra từng Ring trong message. Nếu Ring chưa có trên Cluster, nó thêm Ring vào cluster. Nếu Ring đã có trên cluster, nó kiểm tra version và timestamp của Ring trong message, nếu Ring trong message có timestamp và version lớn hơn Ring hiện tại đang có trong cluster, chúng ta sẽ cập nhật Ring trong cluster. Trong trường hợp còn lại chúng ta drop message.

Tất cả các Resolver trong cluster sẽ dùng chung thông tin của Ring. Thông tin của Ring được lưu trữ tại một file xác định trên Cluster, cũng như được lưu trên Memcache.
