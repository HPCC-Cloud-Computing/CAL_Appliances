# Log Note: Ghi chú những vấn đề gặp phải trong quá trình xây dựng hệ thống

## 18/3/2017

Vấn đề 1: **Giới hạn phạm vi của hệ thống**

Hệ thống được xác định giới hạn phạm vi làm việc như sau:

- Số người dùng hệ thống ở mức độ vừa phải
- Kích thước tệp tin trong hệ thống không quá lớn
- Dung lượng các Cloud Server mà người dùng có là đồng đều với nhau.

Vấn đề 2: **Thêm mới CloudNode vào CloudRing - Các bước xử lý**

1. Tạo CloudID cho Cloud Server mới thêm.
1. Thiết lập CloudRing, thêm Cloud mới tạo vào Cloud Ring theo Chord Protocol. Cập nhật bảng định tuyến cho các Node trong Cloud Ring và cập nhật thông tin định tuyến cho các node nằm ở phía trước và phía sau node mới được thêm vào.
1. Quét danh sách các Replica hiện có trên Successor Node, kiểm tra xem các Replica nào cần phải di chuyển theo Chord Protocol.
1. Chuyển status của Cloud Node mới thêm và Successor Node của nó sang trạng thái **IS\_TRANSFERING\_DATA**. Tạo ra một **Move Data Daemon Process** di chuyển các Replica của các Data Object sai vị trí sang Cloud Node mới.
1. Sau khi di chuyển dữ liệu xong, chuyển lại trạng thái cho Cloud Node mới và Successor Node sang **READY**

Vấn đề xảy ra: Trong Các Replica cần di chuyển có một số Replica không ở trạng thái READY mà đang ở trạng thái UPDATING, vvv....?

Vấn đề 3: **Node Join - Node Leave**

Hệ thống cho phép người dùng xác định Cloud nào sẽ lưu trữ Data Object người dùng tải lên.

Do đó, các replica mà người dùng xác định là ở một Cloud cố định sẽ không bị di chuyển khi add một Node mới vào hệ thống ==> cần có thêm một thuộc tính trong replicaInformation là **Is\_Movable**, xác định Replica này có thể bị di chuyển hay không ?

Vấn đề 4: **Cloud Ring Location**
`
Cloud Ring sẽ được load lên memory để tăng tốc độ truy cập từ Server Thread vào Cloud Ring.

Giải pháp: Singleton design pattern


## 19/3/2017

Vấn đề 1: Từ biểu đồ lớp:

![class_diagram](./images/class_diagram.png)

Và một vấn đề chính của chúng ta
Tại sao lại sử dụng Chord Ring để tìm kiếm xem một Replica có ReplicaID là **x** được lưu trên Cloud Server nào mà không sử dụng bảng để lưu ánh xạ giữa ReplicaID và CloudID?

- Số lượng Cloud Server là nhỏ
- Bỏ qua chi phí tìm kiếm trong Database

Ý nghĩa của Chord Protocol so với việc dùng Bảng là gì ?

## 20/3/2017

Thầy nói là vừa phải code trước những phần có thể code được, vừa phải nghĩ phương pháp giải quyết các vấn đề chưa giải quyết được.

**Vấn đề 1**: Phương pháp tạo ra ReplicaID cho một Replica.

Có 2 hướng giải quyết:

- Hướng 1: Hệ thống không điều khiển, xác định trước Replica sẽ nằm trên CloudServer nào. Sử dụng hàm Hashing phân phối ngẫu nhiên Replica lên các Cloud Server => tạo ra ReplicaID cho Replica bằng cách Hashing tên Replica.
- Hướng 2: Hệ thống thực hiện điều khiển, xác định trước Replica sẽ nằm trên Cloud Server nào trước khi tạo ReplicaID => ReplicaID được hệ thống tạo ra bằng cách ghép CloudID(hoặc Cloud Prefix) rồi ghép thêm kết quả Hashing tên Replica. Lúc này ReplicaID là một **tên có cấu trúc**. Lúc này ReplicaID bao gồm 2 phần: Phần 1 xác định Replica này nằm trên Cloud Server nào. Phần 2 dùng đẻ phân biệt các Replica nằm trong cùng một Cloud Server với nhau.

Note: Chúng ta chỉ có thể sử dụng một trong 2 hướng, không được kết hợp cả 2 hướng với nhau vì sẽ gây ra sự trùng lặp ReplicaID.

Ví dụ: Cần sinh ra replicaID cho replica có tên là **/images/1.png\_replica\_2**. Cloud Ring hiện tại có 4 Cloud Server có CloudID là 5, 18, 23, 29

- Hướng 1: ReplicaID =  Hashing(replica\_name)= Hashing(**/images/1.png\_replica\_2**)= **20**. Với replicaID này, Cloud Server sẽ lưu trữ replica này là Cloud Server có CloudID là 23.
- Hướng 2: Trước khi chúng ta tạo ReplicaID, chúng ta xác định Replica này sẽ nằm trên Cloud Server có CloudID là 18. Như ở hướng 1, chúng ta có Hashing(replica\_name) = 20, do đó replicaID sẽ là **18.20** (Dấu . ở đây nó tương tự như dấu . trong địa chỉ IP). Ở đây, độ dài của ReplicaID là 160 bit thì 80 bit đầu được sử dụng để lưu CloudID (18) và 80 bit sau được sử dụng để lưu replicaID(20) => tên có cấu trúc. Khi đọc ReplicaID này, đầu tiên chúng ta đọc 80 bit đầu để biết được ReplicaID này nằm trên Cloud Server nào, 80 bit sau để định danh cho ReplicaID trong Cloud Server mà trước đó chúng ta xác định.

Như vậy, nếu sử dụng hướng 1, ReplicaID là **20** và Replica được lưu trữ trên Cloud 23. Nếu sử dụng hướng 2, ReplicaID là **18.20**.

**Ý kiến của thầy**: Sử dụng hướng 2. Áp dụng giải thuật để xác định trước Replica sẽ nằm trên Cloud Server nào rồi mới tạo ReplicaID cho Replica, không sử dụng phương pháp phân phối ngẫu nhiên.

**Vấn đề 2**: Một trong những bài toán cần giải quyết trong hệ thống là bài toán sau: Cho một Replica có ReplicaID là **x**, tìm ra CloudID của Cloud Server nào đang chứa Replica này.

Dựa vào 2 hướng tạo ReplicaID đã nêu ở phần trên, bài toán này có 2 hướng giải quyết khác nhau.

**Với hướng 1**: tạo ReplicaID bằng cách Hashing(Replica_Name) - Phân phối ngẫu nhiên, có 2 cách giải quyết:

- Cách 1: Sử dụng Chord Protocol để thực hiện lookup xem ReplicaID này đang nằm trên Cloud Server nào?
- Cách 2: Sử dụng cơ sở dữ liệu để lưu trữ ánh xạ giữa ReplicaID-CloudID (tạo thêm trong cơ sở dữ liệu 1 quan hệ **ReplicaLocation(ReplicaID, CloudID)**)

Vấn đề trong hướng này: Chứng minh rằng cách sử dụng Chord Protocol để Lookup(Cách 1) có hiệu quả hơn việc sử dụng cơ sở dữ liệu để lưu trữ ánh xạ (ReplicaID-CloudID) (cách 2) ?(*)

**Quan điểm của thầy trong vấn đề (*)**: Muốn chứng minh cách 1 tốt hơn cách 2, phải chứng minh hệ thống có tính phân tán. Khi đó cách 1 sẽ tốt hơn cách 2 ở chỗ: Thông tin định tuyến không bị tập trung vào 1 thành phần trong hệ thống (Cơ sở dữ liệu) mà được phân tán ra các node trong hệ thống ==> Nâng cao tính **high - availability** và khả năng chống lỗi - **fault-tolerance**, đồng thời hệ thống có tính phân tán, chỉ cần sử dụng một số node trong hệ thống là có thể tìm ra vị trí lưu trữ trong ReplicaID, chứ không phải thực hiện mỗi lần tìm kiếm ReplicaID lại truy vấn Cơ sở dữ liệu. Tuy nhiên nếu sử dụng Cách 1 - Chord Lookup Protocol, thì chúng ta phải thiết kế hệ thống theo kiến trúc phân tán ==> Các Cloud Node phải nằm **phân tán** và **độc lập** với nhau, thậm chí là các Cloud Node phải nằm ở trên các Cloud Khác nhau, chứ không phải như hiện tại là tất cả các thông tin về Cloud Ring, tất cả các Cloud Node là các **Referrence Node**, nằm tập trung cơ sở dữ liệu trong thông tin của User. Nếu chúng ta gắn được các Cloud Node Service vào Các Cloud Server vật lý, thì việc sử dụng Chord Ring mới có ý nghĩa trong việc tạo ra tính chất **high - availability** và **fault-tolerance**.

![Chord_Ring_In_Cloud_Server_Node](./images/Chord_Ring_In_Cloud_Server_Node.png)

**Với hướng 2**: Khi sử dụng định dạng tên có cấu trúc cho ReplicaID như **18.20**, thì chúng ta không cần phải thực hiện Lookup nữa, lý do là phần 1 trong ReplicaID đã chỉ rõ ra là ReplicaID này thuộc Cloud Server có CloudID (**18**) nào rồi. Lúc này, chúng ta không cần triển khai Chord Ring để thực hiện việc xác định ReplicaID **x** nằm trên Cloud Server nào nữa.

**Ý kiến của thầy**:

- Thầy muốn sử dụng Chord Ring với các Node trên Ring là Các Data Item, và các DataItem sẽ trỏ tới vị trí các DataItem Node khác trên Ring.

- Góc nhìn của thầy đối với hệ thống, đó là tập các Cloud Server của User là thành phần có tính tương đối cố định, tức là các sự kiện Gắn thêm 1 Cloud Server/ Loại bỏ 1 Cloud Server là rất ít khi xảy ra. Các Node trên Chord Ring là Các Data Item, và các thành phần thường xuyên gia nhập và rời khỏi hệ thống là các DataItem chứ không phải là các Cloud Server.

## 24/3/2017

Thầy yêu cầu mô tả 3 mô hình dưới đây. Sau đó, phân tích và chứng minh mô hình Reference Node là mô hình hiệu quả nhất (theo lý thuyết):

3 Mô hình được đưa ra phân tích là: mô hình VM Ring with Virtual Machine Node, mô hình Cloud Ring with Reference Node và mô hình Mapping (CloudID,ObjectID) by SQL Table.

Các bước mô tả, phân tích và chứng minh cụ thể như sau:

Phần 1: Giới thiệu và triển khai các mô hình khả thi để giải quyết cơ chế Lookup và tương tác với Data Object.

Phần 2: Phân tích, so sánh các mô hình với nhau trên các tiêu chí cụ thể. Sau đó, nêu ra các ưu điểm, nhược điểm của từng mô hình.

Kết luận phần 2: Mô hình được lựa chọn mô hình nào, lý do lựa chọn mô hình đó ?

Phần 3: Phân tích kỹ hơn về mô hình đã lựa chọn

## 25/3/2017

Ý kiến của anh Hiếu:

- Triển khai đầy đủ 3 mô hình thầy đề xuất thành 3 bài viết riêng biệt. Viết chi tiết về các vấn đề mà 3 mô hình phải giải quyết (lookup, update, move data, fault tolerance, replicate, load balance...)
- Về đọc lại xem làm sao để khi người dùng muốn truy cập vào nội dung một data Object, thì hệ thống check được container chứa object đó nằm trong account của người dùng, và object người dùng muốn truy cập nằm trong container trên mà không truy cập vào device chứa nội dung container và account. (Tìm hiểu Swift auditor service)
- Xây dựng mô hình multi-ring, 1 Ring chứa thông tin về các Account - Ring này do hệ thống MCS quản lý, và mỗi 1 account chứa 1 Cloud Server Ring độc lập với nhau.

## 26/03/2017

### Vấn đề 1

Việc chúng ta thiết kế và sử dụng hệ thống hiện tại đang xây dựng để quản lý một loạt các loại đám mây khác nhau của nhiều Cloud Server hạ tầng bên dưới (Các Cloud Server như Swift, Amazon S3) cũng tương tự như việc hệ điều hành Linux thiết kế và xây dựng hệ thống VFS ( Virtual File System) để quản lý một loạt các File System khác nhau của hàng loạt các Device bên dưới

Loại đám mây - Loại File System:  Swift, S3, Google Cloud - NTFS, FAT32, ext3, ext4

Khi sử dụng hệ thống của chúng ta, trên thực tế khi người dùng truy cập vào một Data Object lưu trữ trên hệ thống, hệ thống phải đi qua một lớp Abstraction Layer trước khi truy cập tới Cloud Server thực chứa Data Object mà người dùng muốn truy cập => hiệu năng giảm so với cách truy cập trực tiếp tới Cloud Server.

Mục tiêu về hiệu năng : Thiết kế hệ thống của chúng ta - chính là lớp Abstraction Layer, sao cho thời gian được hệ thống dùng để đi qua lớp abstraction Layer là nhỏ nhất có thể.

Kết luận: Mô hình hiện tại của hệ thống của chúng ta có rất nhiều đặc điểm giống với Linux VFS

### Vấn đề 2

Nếu xét về khía cạnh một đồ án tốt nghiệp đơn giản, thì hệ thống của chúng ta không cần thiết phải xây dựng các cơ chế liên quan tới hiệu năng, cân bằng tải, sao lưu, chống lỗi,... Có quá nhiều tối ưu đã đặt vào hệ thống.

Phạm vi của một đò án tốt nghiệp, theo em nghĩ nếu nhìn theo quan điểm góc nhìn phân tích hệ thống Linux VFS:

Cho phép người dùng tương tác vào các Data Object lưu trên các loại Cloud Server khác nhau theo một phương thức đồng nhất:

- Cho phép người dùng chọn Cloud Server sẽ lưu Data Object, lưa chọn có sao lưu Data Object đó vào một Cloud Server khác hay không ?
- Cho phép người dùng truy cập vào các Data Object lưu trên các loại Cloud Server khác nhau theo một phương thức đồng nhất.
- Cho phép người dùng quản lý trạng thái của Data Object.
- Cho phép người dùng sao lưu - backup Data Object Sang một Cloud Server khác.
- ...

Tất cả mọi dữ liệu quản lý Data Object có thể sử dụng cơ sở dữ liệu để lưu trữ.
Đồ án tốt nghiệp của một kỹ sư chỉ cần phân tích thiết kế, sau đó xây dựng được một hệ thống như trên mà không cần phải tính đến các cơ chế hiệu năng, sao lưu, cân bằng tải, phân tán thì cũng là rất ổn rồi. Chúng ta đang xây dựng quá nhiều các tính năng ở phía bên trên => Quy mô của đồ án là lớn hơn nhiều mức cần thiết.

Đề xuất quá trình trình bày đồ án:

Trình bày về tầng 1: Các con Cloud Server, và các hạn chế hiện tại của các Cloud Server

Trình bày về tầng 2:  Trình bày quy trình xây dựng thư viện Abstraction, các cơ chế CRUD cho Data Object khi hệ thống tích hợp nhiều Cloud Server thuộc nhiều loại Cloud khác nhau - và trình bày mô hình một hệ thống sử dụng thư viện này để tạo ra một ứng dụng cho phép tích hợp nhiều Cloud Server với nhau - Trình bày về CAL và một hệ quản lý nhiều Cloud Server sử dụng CAL.

Trình bày về tầng 3: Các cơ chế tối ưu hóa hệ thống, các tính năng nâng cao như phân tán tải - load balance giữa các cloud Server, cơ chế sao lưu replicate, cơ chế tối ưu hóa hiệu năng, cơ chế sử dụng Message Queue để time-coupling, cơ chế đồng bộ hóa cho các bản sao, cơ chế chống lỗi, cơ chế phục hồi - recovery, .....

Đề xuất của em: Chuyển đồ án sang đặt nặng hướng nghiên cứu hơn ==> Tập trung vào thiết kế của hệ thống, còn sản phẩm minh họa chỉ cần thực hiện được một số tính năng là được.

## 19/04/2017

Vấn đề về folder trong MCS

Trong hệ thống MCS, hôm trước như thiết kế thì chúng ta có tính đến việc cho phép người dùng sử dụng cấu trúc cây thư mục để lưu trữ các Data Object. Tuy nhiên, việc sử dụng cấu trúc cây thư mục có một số vấn đề như sau:

Thứ nhất, nếu cho phép thao tác đổi tên thư mục được xảy ra, thì chúng ta phải sử dụng một phương thức khóa nào đó để ngăn thao tác này được diễn ra khi một file con trong thư mục này đang được tạo ra, hoặc đang được cập nhật nội dung.

Ví dụ: Trong hệ thống có một thư mục **folder1** có địa chỉ tuyệt đối là **/root/media/folder1**. Tại một thời điểm **t** xác định, process **create\_data\_object\_process** trong hệ thống đang trong quá trình tạo ra một file **m1.sql** có kích thước 500 MB trong thư mục này, m1.sql có đường dẫn tuyệt đối là **/root/media/folder1/m1.sql**. Tại thời điểm **t**, process này đang tạo ra replica thứ 2 của file **m1.sql**

Cũng tại thời điểm **t**, người dùng gửi request yêu cầu đổi tên thư mục **folder1** thành **folder2**. Nếu như không có lock, thì thao tác đổi tên thư mục sẽ diễn ra đồng thời, song song cùng một lúc với thao tác tạo file **m1.sql**. Nếu thao tác đổi tên diễn ra nhanh hơn thao tác tạo file **m1.sql**, thì rất có khả năng xảy ra sự không nhất quán trong hệ thống, sẽ có thể xảy ra trường hợp 2 replica đầu tiên của file **m1.sql** sẽ được đổi tên (tên tuyệt đối) thành **/root/media/folder2/m1.sql**, còn replica thứ 3 thì lại có tên là **/root/media/folder1/m1.sql** (Vì thao tác đổi tên xảy ra xong trước khi **create\_data\_object\_process** tạo ra replica 3 cho file **m1.sql**), hoặc cũng có thể xảy ra lỗi, khi process thực hiện đổi tên không tìm thấy replica thứ 3 của file **m1.sql**, vì đơn giản là tại thời điểm process thực hiện đổi tên đi tìm replica thứ 3 này, replica thứ 3 vẫn chưa được tạo ra. (Lý do mà process thực hiện thao tác đổi tên folder phải đi tìm replica thứ 3 của file **m1.sql**, là vì như đã trình bày trong thiết kế, khi thao tác đổi tên được xảy ra trên một folder, thì chúng ta cũng phải đổi tên tất cả các folder/file con nằm trong folder đó, vì MCS lưu file dưới dạng tên tuyệt đối).

Vấn đề tương tự xảy ra khi chúng ta muốn xóa một folder trong hệ thống, chúng ta cũng cần phải có các thao tác đồng bộ, để đảm bảo thao tác xóa folder được thực hiện chỉ khi không còn thao tác đọc/ghi dữ liệu diễn ra trong folder đó, cũng như trong các file/folder nằm trong thư mục đó.

Đề xuất: Không cung cấp hai thao tác đổi tên file/folder và xóa file/folder ? Hoặc thiết kế một cơ chế nào đó cho phép đồng bộ hóa các thao tác trong hệ thống ?

Vấn đề được phát hiện khi em đọc bài viết về Google File System. Họ phải dùng lock để đồng bộ hóa các thao tác tạo mới/đổi tên/xóa/cập nhật/đọc/ghi:

[https://github.com/haminhcong/openstack-manual/blob/master/DistributedSystem/Google_File_Sytem.md#41-qu%E1%BA%A3n-l%C3%BD-namespace-v%C3%A0-locking](https://github.com/haminhcong/openstack-manual/blob/master/DistributedSystem/Google_File_Sytem.md#41-qu%E1%BA%A3n-l%C3%BD-namespace-v%C3%A0-locking)
