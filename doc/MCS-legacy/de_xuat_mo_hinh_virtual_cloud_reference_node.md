# Đề xuất mô hình Virtual-Cloud-Reference-Node

## 1. Vấn đề hiện tại của mô hình Reference Node

Theo thiết kế hiện tại, khi hệ thống hoạt động các Node trên Ring là các Đối tượng nằm bên trong các WSGI Process. Mỗi một User trên hệ thống sở hữu một Cloud Ring riêng biệt. Nội dung được lưu trữ trên Các Node là địa chỉ của Cloud Server mà nó đại diện cho.

Mô hình cơ bản của hệ thống như sau:

![current_architect.png](./images/current_architect.png)

Mô hình triển khai theo HA:

![HA_current_architect.png](./images/HA_current_architect.png)

Vấn đề của mô hình hiện tại:

- Các Node là Reference Node, do đó chúng tồn tại như các Đối tượng nằm trên các Process, do đó mỗi một Process cần có một Ring => Khi Cấu hình thay đổi (Có một cloud server thêm vào / ra đi) thì Cấu hình ring thay đổi => Cập nhật tất cả các Ring có trên các Node trong hệ thống, tương tự như Rebalancing trong Swift.
- Cần chứng minh với các vấn đề đặt ra trong hệ thống (Lookup Data Object, Distributed Data Object in several Cloud Servers,Rebalance when new node added... ) thì Chord Ring có hiệu quả hơn các phương pháp khác. Phương pháp được đưa ra so sánh, đó là lưu trữ **Mapping (CloudID,Data\_ObjectID)** bằng một SQL Table

- Vấn đề chống trùng lặp Cloud Server: Không có cách nào để khẳng định rằng, tất cả các Replica của 1 Data Object nằm trên các Cloud khác nhau bằng 1 cơ chế cố định. Giải pháp hiện tại đưa ra là (*):

    - Tạo ra các replicaID cho một Data Object. Sau đó kiểm tra xem replicaID này nằm trên Cloud Server nào.
    - Nếu Cloud Server mà replicaID này được chon nằm trên đã chứa 1 replica trước đó của Data Object, chúng ta không sử dụng ReplicaID này mà chuyển qua sử dụng replicaID khác.

Ví dụ về giải pháp chống trùng lặp: Tên của Data Object cần lưu trữ là **X.png**, cần sao lưu **X.png** với hệ số sao lưu k= 2. ReplicaID đầu tiên được tạo ra là **RID\_1** = hash(**X.png\_replica\_1**) được lưu vào Cloud Server có CloudID là **CID\_1** (Replica đầu tiên không bao giờ bị trùng lặp). Bây giờ chúng ta thử nghiệm RepliaID thứ 2 là **RID\_2** = hash(**X.png\_replica\_2)** rồi xem với ReplicaID = **RID\_2** thì Replica sẽ nằm trên CloudServer nào nào. Nếu **RID\_2** cũng nằm trên **CID\_1**, tức là đã xảy ra trùng lặp, thì chúng ta không dùng replicaID này, dẫn tới việc chúng ta phải thử nghiệm các ReplicID khác, cho đến khi ReplicaID mà chúng ta sinh ra theo quy tẵc sẽ đặt trên một CloudServer khác với Cloud Server **CID\_1**. Ví dụ, nếu như đến lần thử thứ 5 **RID\_5** = hash(**X.png\_replica\_5)** mới nằm trên một Cloud Server khác, ví dụ **RID\_5** nằm trên **CID\_3**, thì lúc đó chúng ta mới chọn ra được 2 ReplicaID cho 2 replica cần sao lưu của **X.png**

Khi số lượng Replica cần sao lưu là k = 3,4,5... Thì vấn đề tương tự xảy ra. Vi vậy, vấn đề của giải pháp hiện tại (*) là:

- Chưa tối ưu. Chúng ta không biết số lượng chính xác số các ReplicaID cần phải thử là bao nhiêu để có được **k** ReplicaID phù hợp để lưu vào **k** Cloud Server khác nhau.
- Chúng ta phải lưu lại các Replica phù hợp của Data Object trên vào hệ thống. Như ở ví dụ trên, chúng ta phải lưu 2 Replica có name là **X.png\_replica\_5** và **X.png\_replica\_3** vào cơ sở dữ liệu
- Khi sinh ra quá nhiều các RepliaID và thử nghiệm như vậy, thì 1 tính chất của Chord, đó là phân phối tự nhiên bị mất đi (do chúng ta cứ thực hiện việc chọn RID quá nhiều lần). Tuy nhiên nếu không chọn ReplicaID, thì chúng ta không đảm bảo rằng **k** replica của Data Object này sẽ nằm trên **k** Cloud Server khác nhau.

Swift Ring xử lý tốt hơn vấn đề trùng lặp so với Chord Ring.

- Vấn đề về việc Remove Cloud Node: Khi gỡ bỏ 1 node hệ thống, xảy ra khả năng theo quy luật của Chord, một Replica của Data Objec **x** trên node bị gỡ bỏ sẽ chuyển về nằm cùng một Replica khác của x trên Successor của Node bị gỡ bỏ => Vấn đề trùng lặp tiếp tục xuất hiện. Giải pháp là chúng ta phải tạo lại ReplicaId cho replica này ???

Một số ý tưởng về các ưu điểm của mô hình hiện tại:

- Khi thêm các Data Object vào hệ thống, cơ chế tự nhiên của Chord Ring cho phép phân phối đều các Data Object lên các Node trong Ring. Nếu chúng ta muốn hệ thống cũng có tính chất này khi sử dụng phương pháp SQL Table Mapping, thì mỗi lần thêm mới 1 Data Object, chúng ta lại phải thực hiện một khối lượng tính toán lớn để chọn ra Cloud Server nào phù hợp để lưu trữ Data Object mới. Trong trường hợp Có nhiều Data Object cùng thêm vào hệ thống trong 1 khoảng thời gian ngắn, thì khó có khả năng chúng ta duy trì được tính phân phối đều cho hệ thống.

- Lượng dữ liệu cần lưu trữ so với SQL Table Mapping là rất nhỏ.
- Khi có sự kiện một Node thêm vào hoặc rời khỏi hệ thống, Ring sẽ thực hiện công việc cân bằng lại Ring. Cơ chế cân bằng của Chord Protocol không quá phức tạp, và số lượng Data Object cần di chuyển để tạo ra sự cân bằng giữa các Node là gần như tối thiểu. Việc thực hiện cơ chế cân bằng tải khi thêm vào/ gỡ bỏ 1 node với phương pháp lưu trữ SQL Table Mapping yêu cầu cần phải xử lý tính toán lớn trên toàn bộ hệ thống, cùng với đó là việc phải cập nhật lại giá trị các entry trong bảng.

- Khi có sự thay đổi trong hệ thống, việc cập nhật Chord Ring là nhanh hơn rất nhiều so với việc cập nhật cơ sở dữ liệu.

- Kích thước rất nhỏ của Ring so với Database cho phép chúng ta có thể load trực tiếp Chord Ring lên RAM để tăng tốc độ truy cập vào Ring, do kích thước của Chord Ring là nhỏ, còn với CSDL, việc này là bất khả thi, nhất là trong trường hợp hệ thống có số lượng Object lên tới hàng triệu Object => SQL phải lưu trữ hàng triệu Record tương đương với số lượng Object trên bảng=> Không đủ RAM để lưu trữ Database.

Các đề xuất cải tiến mô hình hiện tại đang sử dụng:

- Virtual Node: Sử dụng nhiều Node ảo thay vì một node tham chiếu tới cùng một Cloud Server để làm tăng số Cloud Node trên hệ thống => Tăng tính chất phân phối phân tán cho hệ thống. Virtual Node có được đề cập trong bài báo Chord.

- Virtual Node number base Cloud Server Weight: Dung lượng Cloud Server đang xét càng lớn thì số lượng Node trên Ring tham chiếu tới Cloud Server này càng nhiều. Ví dụ Cloud Server có dung lượng 300GB sẽ được 3 virtual Node tham chiếu tới, Cloud Server có dung lượng 900 GB sẽ được 9 virtual node tham chiếu tới

## Giải pháp phòng ngừa các ReplicaID cùng nằm trên một Cloud Server

Một số ý tưởng giải quyết vấn đề trùng lặp CloudID trên hệ thống khi sử dụng Cơ chế Chord Ring

Như đã trình bày ở các phần phía trên, các vấn đề xảy ra khi hệ thống sử dụng cơ chế Chord Ring, đó là vấn đề làm sao để các Replica của 1 Data Object được phân phối lên các Cloud Server khác nhau ? Giải pháp hiện tại đang làm là phải thử các ReplicaID và phải lưu lại các Replica Name đã chọn được => xảy ra các vấn đề liên quan tới bottleneck và failure pointer ở Database Node. Phần này sẽ trình bày 1 số ý tưởng có khả năng giải quyết các vấn đề này.

**Ý tưởng 1 - Sử dụng ý tưởng gom nhóm và virtual node của Swift** - Lấy cảm hứng từ ý tưởng mapping partition Replica - Device được sử dụng trong Swift ring, Chúng ta xây dựng một mô hình Chord ring mới, với cấu hình cố định số Replica của 1 Data Object là **k** theo các bước sau:

1. Tạo ra cho mỗi một Cloud Server **i** trong tập các Cloud Server **k\_i** các _virtual\_cloud_, các _virtual\_cloud_ sẽ tham chiếu tới Cloud Server **i**. Giá trị **k\_i** tỉ lệ thuận với Cloud Server Weight và hệ số _virtual\_factor_
1. Gom **k** virutal\_cloud vào 1 Node, sao cho **k** virtual\_cloud này tham chiếu tới các Cloud Server đôi một phân biệt nhau theo một thuật toán nhất định, ta được một tập các Node.
1. Xếp các Node lên Chord Ring.

Nếu sử dụng phương pháp này, chúng ta không cần lưu lại các ReplicaID nữa.

**Ví dụ cho ý tưởng**:

Đầu vào:

- 3 Cloud Server S1 - 100 GB (weight=1), S2 - 200GB (weight=2), S3 - 100 GB (weight=1)
- Hệ số _virtual\_factor_ = 4
- Hệ số Replica x = 2

Xử lý:

1. Bước 1: Tạo Virutal Cloud cho các cloud server:
    - Tạo các _virtual\_cloud_ cho S1: w1*_virtual\_factor_ = 4: **S1\_1; S1\_2; S1\_3; S1\_4**
    - Tạo các _virtual\_cloud_ cho S2: w2*_virtual\_factor_ = 8: **S2\_1; S2\_2; S2\_3; S2\_4; S2\_5; S2\_6; S2\_7 ;S2\_8**
    - Tạo các _virtual\_cloud_ cho S3: w3*_virtual\_factor_ = 4: **S3\_1; S3\_2; S3\_3; S3\_4**
1. Bước 2: Tạo các Node từ tập các virtual\_cloud. Ta có 16 _virtual\_cloud_, hệ số replica x = 2, do đó ring có 16/2 = 8 Node:

    - Node1: S1\_1; S2\_1
    - Node2: S3\_1; S2\_2
    - Node3: S1\_2; S2\_3
    - Node4: S3\_2; S2\_4
    - Node5: S1\_3; S2\_5
    - Node6: S3\_3; S2\_6
    - Node7: S1\_4; S2\_7
    - Node8: S3\_4; S2\_8

1. Bước 3: Xếp 8 Node vừa được sinh ra lên Chord Ring.

![propose_new_architect.png](./images/propose_new_architect.png)

Sau bước này, chúng ta thiết lập thành công Ring cho hệ thống.

Khi sử dụng Ring này, một object đi vào sẽ được Hashing ID theo tên và dựa vào Chord Protocol để xác định xem Object này tương ứng với node nào trên Ring. Giả sử Object **x** có HashID có Successor node là Node 5, thì chúng ta sẽ lưu và lấy các Replica của **x** trong Node 5. như chúng ta thấy, Node 5 có 2 Virtual Node ánh xạ tới Cloud Server S1 và S2, do đó 1 Replica của x sẽ được lưu trên S1, replica còn lại của x sẽ được lưu trên S2. Tương tự, nếu **x** có HashID có Successor node là Node 6, thì 1 Replica của x sẽ được lưu trên S2, replica còn lại của x sẽ được lưu trên S3.