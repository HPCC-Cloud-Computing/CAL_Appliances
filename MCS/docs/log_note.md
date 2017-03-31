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