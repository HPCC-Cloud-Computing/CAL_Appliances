# Proposal Solution For Create And Distributed Ring Problem In MCOS System

Trong quá trình xây dựng hệ thống MCOS, một vấn đề xuất hiện cần phải giải quyết là: Làm sao để thực hiện thao tác tạo Ring và phân phối Ring được tạo ra tới các Cluster trong hệ thống MCOS, trong điều kiện trạng thái của hệ thống không ổn định mà thay đổi liên tục. Mô tả chi tiết về vấn đề được phát biểu như sau:

Tại thời điểm t, người quản trị hệ thống gửi request lên một trong các Cluster trên hệ thống yêu cầu hệ thống tạo Ring. Tại thời điểm này,đối với với Cluster nhận request, đang có **x** Cluste, và trong **x** Cluster này có **x1** Cluster đang ở trạng thái Active, và **x2** Cluster đang ở trạng thái InActive. Tại thời điểm **t + delta\_t** sẽ có thêm một cluster kết nối vào hệ thống. Tại thời điểm **t +delta\_t\_i** một Cluster trong số các Cluster đang Inactive sẽ kết nối trở lại hệ thống. 

Vấn đề cần giải quyết ở đây là làm sao để Các Cluster Inactive sau khi kết nối trở lại hệ thống, cũng như các Cluster mới kết nối tới hệ thống nhận được Ring được tạo ra tại thời điểm **t**. Một vấn đề khác đi cùng vấn đề này, đó là khi một Ring nào đó được cập nhật, chúng ta cũng cần phải gửi Ring mới tới các Cluster trên hệ thống.

Đề xuất giải pháp mới:

Trên Database của mỗi cluster sẽ duy trì cơ sở dữ liệu về các Ring và trạng thái của Ring tại các cluster trên hệ thống:

![cluster_table.png](./images/cluster_table.png)

Dựa trên 3 table này, tại một cluster bất kỳ trong hệ thống có thể xác định được với 1 Ring **x** đã có bao nhiêu cluster có được Ring này. Từ đó xác định ra các Ring chưa có thông tin về Ring này.

Giải thuật được xây dựng như sau: Định kỳ sau khoảng thời gian delta_t, tại 1 cluster **x** trên hệ thống sẽ tiến hành kiểm tra thông tin từ cơ sở dữ liệu, từ đó xác định với từng Ring mà nó có đã có bao nhiêu cluster có được thông tin về Ring đó. Xác định ra đối với Cluster đang xét thì các cluster nào chưa có thông tin về Ring này, xem trong các cluster này các cluster **k** nào đang ở trạng thái Active, thì cluster **x** sẽ gửi thông điệp chứa thông tin về ring tới cluster **k**.

Một cluster nhận được thông điệp chứa Ring sẽ thực hiện 2 công việc:

- Nếu Ring chưa có trong Cluster đó, tiến hành thêm Ring đó vào hệ thống.
- Nếu cluster gửi Ring chưa có trong dánh sách các Cluster đã cập nhật Ring (bảng **Cluster_Table**), thêm cluster gửi Ring vào table này.

Thuật toán dừng lại đối với Ring **i** nếu tại cluster **x** bất kỳ trên hệ thống, cluster **x** đã biết được rằng các cluster khác đã có được Ring **i**.

Độ phức tạp của thuật toán là O(**m**x**n^2**), với m là số lượng Ring, và n là số lượng cluster có trong hệ thống.

## Update - 18/10/2017

Hôm nay em đã suy nghĩ lại về vấn đề tạo ring và phân phối ring. Em mới nhìn nhận lại thì có 1 vấn đề sau với các Ring trong hệ thống, đấy là mỗi Ring trong hệ thống đều là một tài nguyên chia sẻ chung trong cluster. Vì vậy em nghĩ là em phải có biện pháp để bảo vệ và chỉ cho phép 1 ring được tạo/cập nhật bởi 1 cluster trong một thời điểm t xác định, tức là phải thực hiện lock và unlock quyền được tạo/cập nhật 1 ring trước khi thực hiện tạo ring. Lý do là bởi vì như sau:

Giả sử trên hệ thống có các cluster 1,2,3,4,5,6,7,8,9,10. Tại thời điểm t, hệ thống bị phân mảnh thành 2 mảnh 1,2,3,4,5,6 và mảnh 7,8,9,10 (các cluster trong cùng 1 mảnh nói chuyện được với nhau nhưng không nói chuyện được với các cluster ở mảnh kia). Nếu chúng ta cho phép nhiều cluster đồng thời được tạo/cập nhật một ring cùng 1 lúc , thì nếu tại thời điểm t+1 xảy ra sự kiện 2 admin cùng thực hiện gửi request tạo account\_ring tới cluster 1 và clust 8 với 2 thông số khác nhau, thì sau khi các cluster xử lý request của 2 admin, trên hệ thống sẽ tồn tại 2 account\_ring khác nhau.  Nếu vậy tại thời điểm t+2, khi 2 mảnh kết nối trở lại với nhau, ring nào trong 2 account\_ring trên sẽ trở thành accout\_ring của toàn bộ hệ thống.

Theo quan điểm của em, thì quá trình tạo và cập nhật 1 ring xác định lên các cluster trên hệ thống phải được tiến hành như sau để đảm bảo tính chính xác và đúng đắn của hệ thống.

1. Admin gửi request tạo **ring x** lên một Cluster.
2. Cluster nhận request tạo ring acquire lock từ hệ thống.
3. Nếu cluster acquire lock thành công, system\_lock sẽ bật trên **ring x**. Cluster tiến hành tạo ring.
4. Cơ chế cập nhật ring sẽ thực hiện việc populate ring x tới tất cả các cluster trên hệ thống.
5. Hệ thống sẽ lựa chọn ra 1 cluster làm leader. leader cluster sẽ thực hiện việc định kỳ kiểm tra xem 1 ring đã được cập nhật tới tất cả các cluster trên hệ thống hay chưa, và timeout của ring đó ( ví dụ chúng ta quy định sau khi ring x có mặt trên tất cả các cluster trên hệ thống 1 ngày, thì mới được phép tiếp tục cập nhật ring x). Nếu thỏa mãn rồi thì leader cluster mở khóa - release cho ring x.

Có 2 vấn đề mà em muốn thầy và anh góp ý kiến:

- **Vấn đề 1**: làm sao để acquire\_lock cũng như lựa chọn leader cluster, trong điều kiện hệ thống biến đổi trạng thái liên tục. Em đang dự định sử dụng zookeeper để giải quyết 2 vấn đề này. Em muốn xin ý kiến thầy với anh là dùng zookeeper trong trường hợp này liệu có ổn không ạ.

- **Vấn đề 2**: Cơ chế cập nhật ring em đang dự định thực hiện như sau:

- Các cluster sẽ có một cơ sở dữ liệu chia sẻ chung - chính là nơi lưu trữ keystone database của authentications service. Share database duy trì một danh sách theo dõi tình trạng cập nhật của các ring.
- Định kỳ, leader cluster sẽ kiểm tra một ring xem có bao nhiêu cluster đã được cập nhật ring đó. Lúc này xảy ra 2 trường hợp:

- TH1: Leader Cluster đã có ring: Leader Cluster sẽ thực hiện việc gửi Ring tới các Cluster chưa có ring và đang active. Sau đó các Cluster nhận được Ring sẽ reply cho Leader Cluster, Leader Cluster ghi các cluster đã nhận được ring vào danh sách đã được cập nhật ring.
- TH2: Leader Cluster chưa có ring: Leader Cluster sẽ thực hiện việc lấy Ring từ một trong số các cluster đã có Ring và đang ở trạng thái ACTIVE, sau đó thực hiện tiếp tục như trường hợp 1.
- Thuật toán kết thúc khi tất cả các cluster đã đều ở trong danh sách được cập nhật ring.

## 25/10 Rewrite proposal for create and distribute ring

Để giải quyết bài toán tạo ring và phân phối ring, chúng ta cần 2 luồng hoạt động sau:

- Luồng hoạt động 1: Luồng hoạt động của cluster X nào đó trong hệ thống xử lý request yêu cầu tạo/cập nhật ring T do một User A gửi tới X.

1. X xin lock tạo/cập nhật ring từ hệ thống.
2. Xảy ra 2 trường hợp:
    2.1 X không xin được khóa, X thông báo trở lại cho User A Ring T đang được một người khác tạo/cập nhật trên hệ thống, yêu cầu User A thực hiện lại thao tác vào lúc khác.
    2.2 X xin được khóa, lúc này trên toàn bộ hệ thống, ring T bị lock tạo/cập nhật. X tiếp tục thực hiện bước 3 và 4:
3. X thực hiện tạo ring T từ dữ liệu của người dùng, sau đó X thêm danh sách theo dõi cập nhật Ring T vào shared database.
4. X gửi response cho người dùng thông báo Ring T đã được tạo và đang được phân phối sang các cluster khác trên hệ thống.

- Luồng hoạt động 2: Phân phối ring.

Kịch bản: Trên mỗi cluster X ta có **m monitor\_process** có id phân biệt với nhau, có n cluster trên hệ thống. Ý tưởng được đưa ra ở đây là cần chọn ra chính xác 1 trong số **m*n** process này để thực hiện công việc phân phối ring tới các cluster và mở khóa tạo/cập nhật ring, chúng ta gọi id của process này là **t1**.  
Để thực hiện ý tưởng trên, cần có 1 cơ chế đề thực hiện việc lựa chọn **t1** cũng như lưu trữ phân tán giá trị **t1**, mà lần trước là em đề xuất sử dụng zookeeper.Sau đó, mỗi process trong **m*n** process trên chạy 1 chương trình với nội dung như sau:

Lặp vô hạn (cho đến khi process bị dừng) 4 thao tác sau:

    1. Kiểm tra xem giá trị **t1** là bao nhiêu bằng.
    2. Xảy ra 2 trường hợp:
        -TH2.1: **t1** chưa được thiết lập, thực hiện cơ chế chọn t1 - cơ chế election trong hệ phân tán.
        -TH2.2: **t1 đã được thiết lập**, thực hiện kiểm tra xem giá trị của process hiện tại có phải là t1 hay không ?
            TH2.1 Nếu không phải là t1, chuyển xuống thực hiện bước **sleep**
            TH2.2 Nếu là t1, thực hiện các bước 3,4 dưới đây để phân phối ring và mở khóa tạo/cập nhật ring T:

    3. kiểm tra xem 1 ring đã được cập nhật tới tất cả các cluster trên hệ thống hay chưa bằng cách kiểm tra shared database. 
        TH3.1: Nếu chưa hoàn tấp thì xác định các cluster chưa được cập nhật ring, lấy ring từ các cluster đã được cập nhật rồi gửi tới các cluster chưa được cập nhật mà đang active. Sau đó dựa trên phản hồi từ các cluster này mà cập nhật danh sách các cluster đã cập nhật ring T trên shared database.
        TH3.2: Nếu đã cập nhật xong, thực hiện việc mở khóa tạo/cập nhật ring.

    4. Sleep 5 giây

Các giả thiết được đặt ra:

- zookeeper đảm bảo rằng trong toàn bộ n cluster trên hệ thống sẽ chỉ có tối đa 1 process được chọn ra trong  **m*n** process tại bất kỳ thời điểm nào, trong mọi trường hợp.