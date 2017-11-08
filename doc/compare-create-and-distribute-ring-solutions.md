# Compare create and distribute ring solutions

Bài viết này so sánh 2 hướng tiếp cận strictly và hướng tiếp cận concurrency đối với bài toán tạo và cập nhật ring. Ring được xét trong bài viết này là account ring.

## Đặc điểm cơ bản của 2 phương pháp

- Phương pháp strictly đã được trình bày ở bài viết trước:
    - Cho phép tối đa 2 account ring được tồn tại trên hệ thống tại 1 thời điểm (previous ring và current ring).
    - Chỉ có tối đa 1 user được tạo ring tại một thời điểm, nếu hệ thống nhận được nhiều hơn 2 request tạo ring tại cùng 1 thời điểm, chỉ có tối đa 1 request được accept, các request còn lại bị reject.
    - Trong thời gian từ lúc yêu cầu tạo/cập nhật ring x được accept cho tới khi ring x nó phân phối xong tới các node, cũng như nó cập nhật data, đồng bộ hóa các dữ liệu liên quan vvv.... xong thì các yêu cầu tạo/cập nhật ring x từ client gửi tới bị từ chối/reject. Sau thời gian này, hệ thống mới mở khóa cho phép tiếp tục tạo/ cập nhật ring.
- Phương pháp concurrency:
    - Cho phép nhiều ring (có thể coi là không giới hạn số lượng) được tồn tại trên hệ thống tại cùng 1 thời điểm.
    - Cho phép nhiều user cùng đồng thời tạo/cập nhật 1 ring tại bất kỳ thời điểm nào trong lúc hệ thống đang hoạt động.

Với 2 yêu cầu khác nhau được đặt ra cho 2 phương án chúng ta cần phải xác định xem ưu điểm nhược điểm của 2 phương pháp như thế nào để chọn ra phương án phù hợp nhất cho hệ thống. 

Vấn đề liên quan tới phương pháp tạo và cập nhật ring được đưa ra phân tích ở đây là:

- Giải thuật đồng bộ dữ liệu đi kèm với phương án.

Sau khi đề xuất giải thuật đồng bộ đi kèm với 2 phương án trên, chúng ta sẽ xem xét 2 phương án trên 2 tiêu chí đánh giá sau:

- Mức độ nhất quán của dữ liệu trên hệ thống khi sử dụng phương án.
- Tính sẵn sàng của hệ thống khi sử dụng phương án.

## Giải thuật đồng bộ dữ liệu đi kèm với phương án strictly

Thiết kế đề xuất của giải thuật đồng bộ dữ liệu cho phương án strictly.

Trong phương án strictly, sau khi version mới của ring x được tạo ra trên hệ thống, chúng ta sẽ có 2 version của một ring. 2 version của ring này có cấu hình khác nhau, do vậy khi lookup trên 2 ring này có thể cho hệ thống kết quả khác nhau.

Ví dụ, xét trường hợp đang có 2 user khác nhau trên hệ thống đồng thời gửi yêu cầu xem danh sách các container của **user\_x** lên 2 cluster 3 và 5. Lúc này cluster 3 đang có 2 version của account ring  là **a\_x** (version cũ) và **a\_y** (version mới), còn cluster 5 có version **a\_x** của account ring. Lúc này có thể xảy ra trường hợp khi **user\_x** truy vấn địa chỉ của file chứa danh sách các container của user đó, thì **a\_x** trả về kết quả là tập cluster (1,3,5), trong khi  **a\_y** trả về kết quả là tập cluster (2,4,7). Vậy server sẽ đọc kết quả từ tập cluster nào trong 2 tập cluster trên để trả về kết quả cho người dùng ?

Xét 1 ví dụ khác, đó là trường hợp 2 user cùng sử dụng account **user\_x** gửi request tạo container mới lên 2 cluster 3 và 5. Lúc này câu hỏi đặt ra là thông tin về container mới sẽ được ghi lên các account file ở cluster (1,3,5) hay các account file ở cluster (2,4,7)? 

Giải pháp đồng bộ hóa khi hệ thống đang có 2 version của 1 ring cùng 1 lúc:

- Tại các cluster có 1 version của account ring, việc lookup vẫn thông qua version cũ.
    - Thao tác đọc:
    - Thao tác ghi:
- Tại các cluster có 2 version của account ring, chúng ta xét 2 thao tác đọc/ghi các account file:
    - Thao tác đọc: khi một cluster nhận được request, nó tiến hành lookup trên cả 2 ring, lúc này nó sẽ được 2 **account\_file**  là a1 và a2. Cluster tiến hành tổng hợp kết quả của cả a1 và a2 lại để trả về cho người dùng theo một trong số các giải pháp đồng bộ.
    - Thao tác ghi:

- Cơ chế làm việc của synchronization service: