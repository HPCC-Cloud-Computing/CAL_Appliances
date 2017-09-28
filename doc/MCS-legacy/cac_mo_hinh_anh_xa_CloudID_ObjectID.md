# Phân tích và lựa chọn mô hình ánh xạ Data Object - Cloud Server cho hệ thống MCS

Một trong những bài toán quan trọng nhất trong hệ thống MCS, đó là bài toán xây dựng cơ chế phân giải tên ( **object naming** - **name resolution**) cho các Data Object lưu trữ trong hệ thống. Nội dung của bài toán này được mô tả thông qua các vấn đề sau:

- Khi người dùng muốn lưu trữ một Data Object có tên là **x** lên hệ thống, Data Object (trên thực tế là các Replica của Data Object) này sẽ được lưu trữ Ở Cloud Server nào ?
- Khi người muốn lấy nội dung của một Data Object **x** thông qua tên của Data Object đó, làm sao để hệ thống phân giải tên của **x** để tìm ra các Replica của **x** đang lưu trữ tại vị trí nào (Cloud Server nào) trên hệ thống?

Bài viết này phân tích và đưa ra một số giải pháp giải quyết bài toán này. Dựa trên các giải pháp này, chúng ta sẽ tiến hành xây dựng các mô hình ánh xạ Data Object - Cloud Server cho hệ thống MCS. Sau đó, chúng ta sẽ so sánh các mô hình với nhau, đồng thời phân tích các ưu điểm và nhược điểm của từng mô hình, từ đó tìm ra mô hình phù hợp nhất cho hệ thống MCS.

## Mục lục

<!-- TOC -->

- [Phân tích và lựa chọn mô hình ánh xạ Data Object - Cloud Server cho hệ thống MCS](#phân-tích-và-lựa-chọn-mô-hình-ánh-xạ-data-object---cloud-server-cho-hệ-thống-mcs)
    - [Mục lục](#mục-lục)
    - [1. Các phương pháp giải quyết bài toán phân giải tên trong hệ thống MCS](#1-các-phương-pháp-giải-quyết-bài-toán-phân-giải-tên-trong-hệ-thống-mcs)
    - [2. Mô hình Store Mapping (CloudID,ObjectID) by Database](#2-mô-hình-store-mapping-cloudidobjectid-by-database)
        - [2.1 Giải quyết vấn đề phân phối đồng đều dữ liệu theo dung lượng Cloud Server và sao lưu Data Object](#21-giải-quyết-vấn-đề-phân-phối-đồng-đều-dữ-liệu-theo-dung-lượng-cloud-server-và-sao-lưu-data-object)
        - [2.2 Phương thức lưu trữ và truy cập trạng thái của Data Object và của các Replica](#22-phương-thức-lưu-trữ-và-truy-cập-trạng-thái-của-data-object-và-của-các-replica)
        - [2.3 Phương thức thêm mới, gỡ bỏ một Cloud Server khỏi hệ thống](#23-phương-thức-thêm-mới-gỡ-bỏ-một-cloud-server-khỏi-hệ-thống)
            - [2.3.1 Thêm mới một Cloud Server vào hệ thống](#231-thêm-mới-một-cloud-server-vào-hệ-thống)
            - [2.3.2 Gỡ bỏ một Cloud Server khỏi hệ thống](#232-gỡ-bỏ-một-cloud-server-khỏi-hệ-thống)
        - [2.4 Quản lý thông tin tài khoản người dùng và danh sách các Data Object trong tài khoản người dùng đang thực hiện thay đổi](#24-quản-lý-thông-tin-tài-khoản-người-dùng-và-danh-sách-các-data-object-trong-tài-khoản-người-dùng-đang-thực-hiện-thay-đổi)
    - [3. Mô hình VM Ring with Virtual Machine Node](#3-mô-hình-vm-ring-with-virtual-machine-node)
        - [3.1 Xây dựng cơ chế giải quyết các vấn đề phân phối đồng đều dữ liệu theo dung lượng Cloud Server và sao lưu Data Object](#31-xây-dựng-cơ-chế-giải-quyết-các-vấn-đề-phân-phối-đồng-đều-dữ-liệu-theo-dung-lượng-cloud-server-và-sao-lưu-data-object)
        - [3.2 Phương thức lưu trữ và truy cập trạng thái của Data Object và của các Replica](#32-phương-thức-lưu-trữ-và-truy-cập-trạng-thái-của-data-object-và-của-các-replica)
        - [3.3 Phương thức thêm mới, gỡ bỏ một Cloud Server khỏi hệ thống](#33-phương-thức-thêm-mới-gỡ-bỏ-một-cloud-server-khỏi-hệ-thống)
            - [3.3.1 Thêm mới một Cloud Server](#331-thêm-mới-một-cloud-server)
            - [3.3.2 Gỡ bỏ một Cloud Server](#332-gỡ-bỏ-một-cloud-server)
        - [3.4 Quản lý thông tin tài khoản người dùng và danh sách các Data Object trong tài khoản người dùng đang thực hiện thay đổi](#34-quản-lý-thông-tin-tài-khoản-người-dùng-và-danh-sách-các-data-object-trong-tài-khoản-người-dùng-đang-thực-hiện-thay-đổi)
    - [4. Mô hình Cloud Ring with Reference Node](#4-mô-hình-cloud-ring-with-reference-node)
        - [4.1 Xây dựng cơ chế giải quyết các vấn đề phân phối đồng đều dữ liệu theo dung lượng Cloud Server và sao lưu Data Object](#41-xây-dựng-cơ-chế-giải-quyết-các-vấn-đề-phân-phối-đồng-đều-dữ-liệu-theo-dung-lượng-cloud-server-và-sao-lưu-data-object)
        - [4.2 Phương thức lưu trữ và truy cập trạng thái của Data Object và của các Replica](#42-phương-thức-lưu-trữ-và-truy-cập-trạng-thái-của-data-object-và-của-các-replica)
        - [4.3 Phương thức thêm mới, gỡ bỏ một Cloud Server khỏi hệ thống](#43-phương-thức-thêm-mới-gỡ-bỏ-một-cloud-server-khỏi-hệ-thống)
            - [4.3.1 Thêm mới một Cloud Server](#431-thêm-mới-một-cloud-server)
            - [4.3.2 Gỡ bỏ một Cloud Server](#432-gỡ-bỏ-một-cloud-server)
        - [4.4 Quản lý thông tin tài khoản người dùng và danh sách các Data Object trong tài khoản người dùng đang thực hiện thay đổi](#44-quản-lý-thông-tin-tài-khoản-người-dùng-và-danh-sách-các-data-object-trong-tài-khoản-người-dùng-đang-thực-hiện-thay-đổi)
    - [5. Phân tích và so sánh đặc điểm của các mô hình](#5-phân-tích-và-so-sánh-đặc-điểm-của-các-mô-hình)
        - [5.1 Đánh giá hiệu năng hệ thống và các điểm tắc nghẽn trong mô hình](#51-đánh-giá-hiệu-năng-hệ-thống-và-các-điểm-tắc-nghẽn-trong-mô-hình)
        - [5.2 Khả năng Scaling và tài nguyên sử dụng cho từng mô hình](#52-khả-năng-scaling-và-tài-nguyên-sử-dụng-cho-từng-mô-hình)
        - [5.3 Khả năng chống lỗi và phục hồi](#53-khả-năng-chống-lỗi-và-phục-hồi)
    - [5. Lựa chọn mô hình cơ sở để phát triển hệ thống MCS](#5-lựa-chọn-mô-hình-cơ-sở-để-phát-triển-hệ-thống-mcs)
    - [Tài liệu tham khảo](#tài-liệu-tham-khảo)

<!-- /TOC -->

## 1. Các phương pháp giải quyết bài toán phân giải tên trong hệ thống MCS

Thông tin đầu vào và đầu ra của bài toán phân giải tên trong MCS System là:

- Đầu vào của bài toán là tên của Data Object mà người dùng muốn tương tác. Trong hệ thống, thì tên của một Data Object là tên tuyệt đối và duy nhất. Ví dụ, một Data Object có thể có tên tuyệt đối như sau: **/home/images/images1.png**.
- Đầu ra của bài toán, đó là địa chỉ truy cập của Cloud Server đang chứa replica của Data Object đó.

Như vậy, chúng ta có thể thấy, về cơ bản, mục tiêu của bài toán là: Xây dựng một ánh xạ đơn ánh **f**, sao cho với một Data Object có tên là **x** được nằm trên Cloud Server có địa chỉ truy cập là **y**, thì **f(x) = y**. Trong hệ thống MCS, **f** được gọi là cơ chế mapping giữa Data Object và Cloud Server.

Chúng ta có nhiều phương pháp để xây dựng cơ chế mapping **f**, trong bài viết này, hai cơ chế sau đây được sử dụng:

- Cơ chế mapping bằng Database(DataObjectID, Cloud\_ServerID)
- Cơ chế mapping bằng DistributedHashTable - DHT

Với mỗi một cơ chế mapping ở trên, chúng ta có thể xây dựng được một hoặc nhiều mô hình ánh xạ Data Object - Cloud Server. Mô hình ánh xạ được hiểu là với một cơ chế mapping **A** cho trước, chúng ta sẽ xây dựng một kiến trúc hệ thống bao gồm các đối tượng cụ thể và cách thức tổ chức, liên kết và phối các đối tượng này để thực thi cơ chế mapping **A** trong hệ thống. Tại thời điểm này, chúng ta đưa ra được 3 mô hình khả thi cho 2 cơ chế mapping phía trên là:

- Mô hình VM Ring with Virtual Machine Node
- Mô hình Cloud Ring with Reference Node
- Mô hình Store Mapping (CloudID,ObjectID) by Database

Trong đó, 2 mô hình Cloud Ring with Reference Node và VM Ring with Virtual Machine Node được xây dựng dựa trên cơ chế Distributed Hash Table, còn mô hình Store Mapping (CloudID,ObjectID) by Database được xây dựng dựa trên cơ chế mapping Database(DataObjectID, Cloud\_ServerID).

Như vậy, mô hình ánh xạ Data Object - Cloud Server là kết quả của việc giải quyết bài toán phân giải tên, và nó là nền tảng để xây dựng hệ thống MCS. Tuy nhiên, việc phân tích bài toán phân giải tên chỉ là bước đầu trong quá trình xây dựng mô hình, và công việc này cho chúng ta một bộ khung cơ bản của hệ thống. Do đó,chúng ta phải tiếp tục hoàn thiện mô hình bằng cách xây dựng các cơ chế xử lý các vấn đề khác trong hệ thống như:

- Cơ chế phân phối đồng đều dữ liệu theo dung lượng Cloud Server - data balancing giữa các Cloud Server.
- Cơ chế sao lưu - replicate Data Object.
- Cơ chế quản lý thông tin, trạng thái của một Data Object và thông tin, trạng thái của các Replica của Data Object đó.
- Cơ chế thêm một Cloud Server vào hệ thống, gỡ bỏ một Cloud Server ra khỏi hệ thống.

Trong phần tiếp theo, chúng ta sẽ mô tả chi tiết, và sau đó đi vào xây dựng hoàn thiện 3 mô hình đã được đề xuất.

## 2. Mô hình Store Mapping (CloudID,ObjectID) by Database

Mô hình Store Mapping by Database được xây dựng bằng cách sử dụng cơ sở dữ liệu để lưu trữ ánh xạ (ObjectID,CloudID). Khi chúng ta muốn biết một Data Object có ObjectID là **x** đang ở Cloud Server nào, chúng ta sẽ truy cập vào cơ sở dữ liệu này để tìm ra CloudID tương ứng với ObjectID **x**.

Sau khi phân tích, chúng ta sẽ nhận thấy rằng, thông tin của một Object **x** trong hệ thống không chỉ gói gọn trong đối tượng lưu trữ, mà thực tế bao gồm rất nhiều các thành phần. Để phòng trừ các sự cố xảy ra, thông tin lưu trữ trong **x** cần sao lưu trên nhiều bản sao, được gọi là các Replica. Bên cạnh đó, để hệ thống có thể dễ dàng quản lý **x**, chúng ta cần có ObjectMetadata của **x**. Do vậy, khi chúng ta đi sâu vào phát triển khái niệm Object trong hệ thống, chúng ta sẽ hiểu rằng, về bản chất, thông tin của một Object **x** trong hệ thống bao gồm Object Metadata của x và thông tin lưu trữ trong các Replica của x. Vị trí của một Object trên hệ thống sự là tổng hợp của vị trí của các Replica của Object đó trên hệ thống kết hợp với vị trí của Object Metadata của Object đó trên hệ thống. Trong mô hình này và hai mô hình tiếp theo, chúng ta sẽ phân tích một Data Object thông qua 2 thành phần chính của nó: Object Metadata và các Object Replica. Trong đó, các Object Replica sẽ được chúng ta phân tích trước, và Object Metadata sẽ được phân tích sau ở phần : Phương thức lưu trữ và truy cập trạng thái của Data Object và của các Replica.

Như chúng ta đã nói, một Data Object được sao lưu thành nhiều Replica lưu trên nhiều Server khác nhau, do đó, trên thực tế ánh xạ chúng ta cần lưu trữ trên Database là ánh xạ giữa các Object Replica và các Cloud Server. Để xây dựng ánh xạ này, chúng ta thêm vào ánh xạ hiện tại tham số Replica\_Index xác định chỉ số của Replica trong Object **x**. Lúc này, ánh xạ của chúng ta trở thành Mapping (CloudID, ReplicaIndex, ObjectID), ánh xạ này chỉ ra Replica có index là **i** của Object có ObjectID là **x** sẽ nằm trên Cloud Server nào trong hệ thống.

Replica Mapping này trong hệ thống thực tế có thể có dạng như sau:

| ObjectID      |Replica\_Index | CloudID
| ------------- |:--------------|:-------------
|1              |1              |4
|2              |1              |3
|2              |2              |1
|3              |1              |3
|3              |2              |2
|...            |...            |...

Chúng ta sẽ tiếp tục phát triển mô hình bằng cách phân tích và đưa thêm các cơ chế vào trong mô hình để giải quyết các vấn đề khác trong hệ thống.

### 2.1 Giải quyết vấn đề phân phối đồng đều dữ liệu theo dung lượng Cloud Server và sao lưu Data Object

Điểm khác biệt giữa 2 mô hình sử dụng Ring với mô hình Store Mapping by Database là: Trong 2 mô hình sử dụng Ring, việc một Data Object sẽ được lưu trữ ở Cloud Server nào không do hệ thống điều khiển, mà tuân theo quy luật xác suất và gần như là ngẫu nhiên. Còn trong mô hình Store Mapping by Database, thì việc một Data Object được lưu trữ ở Cloud Server nào hoàn toàn là do hệ thống quyết định.

Một vấn đề khác mà chúng ta cần xử lý, đó là vấn đề sao lưu các Data Object: Một Data Object trên hệ thống cần được lưu trữ trên **k** Cloud Server (k>=2) để đảm bảo rằng dữ liệu trên hệ thống vẫn an toàn ngay cả khi một Cloud Server nào đó gặp sự cố (Ví dụ như nếu khách hàng có một số Swift Cloud Server đặt tại 1 số thành phố hay mất điện chẳng hạn). Thường k được chọn = 3, tức là khi người dùng tải lên một Data Object, thì chúng ta sẽ tạo ra 3 bản sao của Data Object đó và lưu trữ trên 3 Cloud Server khác nhau.

Để thực thi cơ chế phân phối đồng đều dữ liệu theo dung lượng Cloud Server và sao lưu Data Object trong mô hình Store Mapping by Database, chúng ta sẽ duy trì một table **Cloud\_Server\_Information** lưu trữ các thông tin về một Cloud Server của người dùng, cũng như lưu trữ thông tin về lượng dữ liệu hiện tại đang chứa trên từng Cloud Server là bao nhiêu:

| CloudID       | Capacity     |Current Used       |Current Replica number|Status
| ------------- |:-------------|:------------------|:---------------------|:-------------
|1              |50            |15                 |1537                  |ALIVE
|2              |100           |60                 |4505                  |ALIVE
|3              |80            |40                 |3108                  |ALIVE
|...            |...           |...                |...

(Đơn vị của Capacity và Current Used là **GB**)

Sử dụng table trên, hệ thống sẽ quyết định các bản sao một Data Object mới sẽ được lưu trữ trên các Cloud Server nào theo một trong các phương pháp phân phối như round-robin, least-used,...(Người dùng hệ thống sẽ lựa chọn phương pháp phân phối trong file **config.py**). Sau khi các bản sao của Data Object mới được thêm vào, hệ thống nhật lại thông tin của table trên theo kích thước của Data Object vừa được thêm vào hệ thống.

### 2.2 Phương thức lưu trữ và truy cập trạng thái của Data Object và của các Replica

Khi MCS API Server phục vụ các yêu cầu của người dùng liên quan tới việc tương tác với Data Object (như truy cập, cập nhật, xóa bỏ) hoặc khi các deamon của hệ thống hoạt động như deamon thực hiện công việc phục hồi các Replica bị lỗi, thì chúng cần phải kiểm tra xem Object đó và các Replica đang ở trạng thái nào, từ đó đưa ra các quyết định xử lý phù hợp. Do đó, một trong các cơ chế quan trọng cần được xây dựng trong mô hình là cần phải có phương thức lưu trữ và truy cập trạng thái của các Data Object cũng như các Replica của chúng. Trạng thái của các Data Object và của các Object Replica cũng chính là Object metadata của các Data Object trên hệ thống MCS.

Trong mô hình Store Mapping by Database, thông tin về các Data Object và các Replica được lưu trữ trong database dưới dạng các Mapping **Object\_Information** và **Replica\_Information**, trong đó, **Replica\_Information** là sự phát triển tiếp theo của **Replica Mapping**:

Object\_Information Mapping

| ObjectID      |Object Name                            |Status
| ------------- |:--------------                        |:--------------
|1              |/home/images/images1.png               |IS\_CREATING
|1              |/home/data/log_note/install\_note.txt  |READY
|1              |/home/movie/2008.mp4                   |IS\_UPDATING
|...            |...                                    |...

Replica\_Information Mapping

| ObjectID      |Replica\_Index| CloudID     |Status
| ------------- |:--------------|:------------|:-----------
|1              |1              |4            |UPDATED
|2              |1              |3            |UPDATED
|2              |2              |1            |NOT\_UPDATED
|3              |1              |3            |CORRUPTED
|3              |2              |2            |UPDATED
|...            |...            |...

### 2.3 Phương thức thêm mới, gỡ bỏ một Cloud Server khỏi hệ thống

#### 2.3.1 Thêm mới một Cloud Server vào hệ thống

Khi sử dụng phương mô hình Store Mapping by Database, thì khi thêm mới một Cloud Server vào hệ thống, chúng ta chỉ cần tạo ra thông tin quản lý của Cloud Server đó và thêm vào **Cloud\_Server\_Information**

#### 2.3.2 Gỡ bỏ một Cloud Server khỏi hệ thống

Khi gỡ bỏ một Cloud Server khỏi hệ thống, thì chúng ta phải thực hiện việc di chuyển tất cả các Replica của các Data Object đang lưu trữ trên Cloud Server đó sang các Cloud Server còn lại trong hệ thống. Việc di chuyển một Replica của Data Object **x** nằm trên Cloud Server cần gỡ bỏ được thực hiện qua các bước sau:

1. Kiểm tra xem các Replica khác của **x** này nằm ở Cloud Server nào trên hệ thống, sau đó xác đinh danh sách các Cloud Server không chứa replica của **x**.
1. Lựa chọn 1 trong số các Cloud Server không chứa Replica của **x** theo một trong số các phương pháp phân phối (round-robin, least-used,...). Sau đó, copy một Replica từ một Cloud Server chứa replica của **x** sang Cloud Server được chọn, và thêm thông tin quản lý của Replica vừa được copy vào table **Replica\_Information**, đồng thời xóa bỏ thông tin quản lý của replica cũ nằm trên Cloud Server đã bị loại bỏ.

### 2.4 Quản lý thông tin tài khoản người dùng và danh sách các Data Object trong tài khoản người dùng đang thực hiện thay đổi

Trong mô hình  Store Mapping by Database, thông tin tài khoản người dùng được lưu trữ trong database. Các thông tin cần lưu trữ là thông tin xác thực tài khoản trên hệ thống, và danh sách các Cloud Server mà người dùng đó sở hữu. Bên cạnh đó, các thông tin quan trọng khác được lưu trữ trong thông tin tài khoản người dùng, đó là danh sách các Data Object đang thực hiện thay đổi. Lý do mà chúng ta cần có thông tin này là:

Nguyên tắc cần được tuân theo trong việc thiết lập các cơ chế xử lý các yêu cầu của người dùng, đó là hệ thống cần xử lý và phản hồi cho người dùng trong thời gian nhanh nhất có thể. Dựa trên nguyên tắc này, khi thực hiện các thao tác tạo mới, cập nhật, xóa bỏ các Data Object, API Server sẽ chỉ thực hiện các thay đổi lên 1 trong số các Replica đang có trên hệ thống rồi trả lại phản hồi cho người dùng. Giai đoạn còn lại (thực hiện thay đổi lên các Replica còn lại) trong các thao tác này sẽ do các daemon process thực hiện.

Trong quá trình các Data Object được các daemon process tương tác, chúng ta cần quản lý và theo dõi các Data Object này bằng cách duy trì các danh sách Data Object của một User đang thực hiện các quá trình updating, creating, deleting. Các danh sách này nằm trong thông tin tài khoản người dùng trong database chung của hệ thống.

![changing_objects_lists](./images/changing_objects_lists.png)

## 3. Mô hình VM Ring with Virtual Machine Node

Mô hình VM Ring with Virtual Machine Node là mô hình được xây dựng dựa trên nền tảng là Chord Protocol, với các Node trên Chord Logic Ring là các Virtual Machine. Mỗi Virtual Machine tham chiếu và đại diện cho một Cloud Server trên hệ thống. Khi sử dụng mô hình VM Ring cơ bản, hệ thống MCS sẽ có kiến trúc như sau:

![Virtual_Node_Architech](./images/Virtual_Node_Architect.png)

Quá trình phân giải tên Data Object khi hệ thống sử dụng mô hình Virtual Machine Node về cơ bản sẽ diễn ra như sau:

Client sẽ gửi yêu cầu tải về một Data Object có tên là **x** Lên MCS API Server. MCS API Server nhận được request rồi chuyển tiếp request tới một trong các VM Node trên Ring. VM Node này sẽ thực hiện nhiệm vụ Hashing Data Object Name để lấy ra Data\_Object\_ID. Sau đó VM Ring sẽ dựa vào Chord Lookup Protocol để đi tới VM Node là Successor Node của **Data\_Object\_ID** này, Cloud Server được VM Node này đại diện cho chính là Cloud Server chứa Data Object cần tìm. Sau đó VM Node này sẽ gửi trả về cho MCS API Server thông tin của Cloud Server mà nó đang đại diện. MCS API Server gửi thông tin này tới Client, sau đó Client sử dụng thông tin này để kết nối trực tiếp tới Cloud Server để tải về nội dung của Data Object.

### 3.1 Xây dựng cơ chế giải quyết các vấn đề phân phối đồng đều dữ liệu theo dung lượng Cloud Server và sao lưu Data Object

Các đặc điểm quan trọng của mô hình VM Ring mà chúng ta phải quan tâm tới khi giải quyết vấn đề phân phối đồng đều dữ liệu theo dung lượng Cloud Server và sao lưu Data Object trong mô hình VM Ring là:

1. Thông tin trong hệ thống không được lưu trữ trong Store Mapping by Database.
1. Hệ thống không điều khiển việc một Data Object khi được thêm vào hệ thống sẽ nằm trên Cloud Server nào, vị trí của Data Object trên hệ thống do Chord Protocol quyết định.
1. Về mặt lý thuyết, khi sử dụng phương pháp Chord Protocol để phân giải tên, thì xác suất một Data Object có tên tuyệt đối là **x** được một Cloud Server lưu trữ là **1/n**. Điều đó có nghĩa là, trong trường hợp tất cả các Cloud Server mà người dùng có có Dung lượng lưu trữ bằng nhau, thì hệ thống sẽ phân phối đều dữ liệu lên các Cloud Server. Tuy nhiên, vấn đề xảy ra ở đây là dung lượng của các Cloud Server mà người dùng có thường là rất khác nhau,nên hệ thống chưa thể thực hiện việc phân tán tải một cách lý tưởng. Tính chất phân tán tải lý tưởng được thực hiện khi lượng dữ liệu được lưu trữ trên một Cloud Server tỉ lệ thuận với dung lượng của Cloud Server đó.
1. Việc thêm các hậu tố khác nhau vào sau tên của Data Object để tạo ra tên của các Replica không đảm bảo rằng các replica của Data Object đó sẽ nằm trên các Cloud Server khác nhau. Ví dụ, với một Data Object có tên là **/home/images/images1.png**, thì chúng ta không thể đảm bảo rằng 2 Replica có tên là **/home/images/images1.png\_replica1** và **/home/images/images1.png\_replica2** sau quá trình Hashing nằm trên 2 Cloud Server khác nhau với xác suất 100 %

Vậy, với các đặc điểm trên của mô hình VM Ring, vấn đề phân phối đồng đều dữ liệu và sao lưu Data Object được xử lý như thế nào ?

Giải pháp được đưa ra ở đây, đó là sử dụng các phương pháp Virtual Server kết hợp với phương pháp phân phối đồng đều dữ liệu thông qua số lượng Virtual Server ánh xạ tới một Cloud Server. Triển khai cụ thể của giải pháp này như sau:

1. Xác định số lượng VM có trên Ring: m.
1. Xác định số lượng Bản sao - Replica của một Data Object: k.
1. Với mỗi một VM trên Ring, xác định k Virtual Server mà VM đó quản lý sẽ ánh xạ tới k Cloud Server phân biệt nào, với mỗi một Virtual Server sẽ chỉ ánh xạ tới một Cloud Server mà người dùng có. Một Virtual Server được xác định sẽ ánh xạ tới Cloud Server nào dựa trên các thông tin sau:
    - Số lượng các Virtual Server đã ánh xạ tới từng Cloud Server.
    - Dung lượng (weight) của từng Cloud Server.
    - Thuật toán phân phối sử dụng.

![VM_Node_LocalDB_Architect.png](./images/VM_Node_Virtual_Cloud_Architect.png)

Khi triển khai giải pháp này, một Cloud Server sẽ được nhiều Virtual Server ánh xạ tới, số lượng Virtual Server ánh xạ vào 1 Cloud Server tỉ lệ thuận với dung lượng lưu trữ của Cloud Server đó. Đồng thời, giải pháp này đảm bảo rằng một Data Object sẽ được nhân bản thành k bản sao (k>=2) và mỗi bản sao được lưu trữ tại một Cloud Server khác nhau.

### 3.2 Phương thức lưu trữ và truy cập trạng thái của Data Object và của các Replica

Trong mô hình VM Ring, thông tin về các thực thể sẽ không được lưu trữ trong cơ sở dữ liệu tập trung. Do đó, chúng ta cần có một cách khác để lưu trữu thông tin trạng thái của Data Object và của các Replica.

Giải pháp được đưa ra, đó là chúng ta sẽ cài đặt trên mỗi một VM một cơ sở dữ liệu địa phương (local database). Local Database của một VM sẽ lưu trữ thông tin về các Data Object và các Replica của các Data Object đó.

![VM_Node_LocalDB_Architect.png](./images/VM_Node_Virtual_Cloud_With_LocalDB_Architect.png)

Với mô hình này, quá trình Lookup trong hệ thống diễn ra như sau:

1. Client của người dùng gửi Request tới MCS API Server.

1. MCS API Server hashing tên của Data Object người dùng muốn lấy về => lấy được **ObjectID**, sau đó nó gửi Lookup request tới một VM Node trong các VM nằm trên VM Ring, với tham số truyền vào là ObjectID và địa chi của chính MCS API Server đó.
1. VM Node đầu tiên nhận Lookup từ MCS API Server sử dụng Chord Protocol để chuyển tiếp thông tin, cho đến khi Lookup Request được gửi tới Node  tham chiều tới các Cloud Server chứa các Replica của Data Object mà người dùng muốn lấy về ( hay chính là Successor Node của **ObjectID**).
1. Khi VM là Successor Node của ObjectID nhận được Lookup request, nó tiến hành truy cập vào Local Database của nó để kiểm tra trạng thái của Data Object cũng như của các Replica tương ứng với ObjectID chứa trong Lookup Request. Nếu Data Object mà người dùng muốn truy cập ở một trong các trạng thái hợp lệ, VM sẽ kiểm tra và lấy ra thông tin một Replica của Data Object đó đang ở trạng thái UPDATED. Sau đó VM gửi trả về cho MCS API Server thông tin truy cập Cloud Server đang chứa Replica này.
1. MCS API Server gửi trả về cho Client thông tin truy cập của Cloud Server. Client sử dụng thông tin này kết nối trực tiếp với Cloud Server để lấy về nội dung của Data Object.

### 3.3 Phương thức thêm mới, gỡ bỏ một Cloud Server khỏi hệ thống

#### 3.3.1 Thêm mới một Cloud Server

Khi thêm mới một Cloud Server vào hệ thống, chúng ta thực hiện cân bằng lại - rebalancing hệ thống bằng cách chuyển hướng một số Virtual Server ánh xạ tới các Cloud Server hiện tại sang Cloud Server mới.

Ví dụ về quá trình thêm mới một CloudServer:

Trước khi thêm Cloud Server mới, hệ thống có mô hình như sau:

![VM_Node_Add_Cloud_Server_Before](./images/VM_Node_Add_Cloud_Server_Before.png)

Trước khi thay đổi, ta có số lượng Virtual Server ánh xạ tới các Cloud Server là:

Cloud\_Server | Virtual\_Node\_Number
--------------|----------------------
1 | 5
2 | 5
3 | 6
4 | 4
5 | 4

Sau khi thêm Cloud Server 6 vào hệ thống, chúng ta thực hiện thay đổi ánh xạ trên một số Virtual Server trong một số VM để chuyển Virtual Server đó ánh xạ sang Cloud Server 6. Các Virtual Server sẽ thay đổi ánh xạ được lựa chọn theo một trong các phương pháp phân phối như Round Robin, most Used...:

![VM_Node_Add_Cloud_Server_After](./images/VM_Node_Add_Cloud_Server_After.png)

Cloud\_Server | Virtual\_Node\_Number
--------------|----------------------
1 | 4
2 | 3
3 | 5
4 | 4
5 | 4
6 | 4

Sau khi thay đổi ánh xạ của các Virtual Server, chúng ta cần di chuyển các Replica từ Cloud Server cũ sang Cloud Server mới

#### 3.3.2 Gỡ bỏ một Cloud Server

Trong mô hình VM Ring, để gỡ bỏ một Cloud Server khỏi hệ thống, chúng ta cũng thực hiện công việc rebalancing với một phương pháp phân phối xác định tương tự như trong trường hợp thêm mới Cloud Server.

Ví dụ, trước khi hệ thống gỡ bỏ Cloud Server 3:

![VM_Node_Add_Cloud_Server_Before](./images/VM_Node_Add_Cloud_Server_Before.png)

Cloud\_Server | Virtual\_Node\_Number
--------------|----------------------
1 | 5
2 | 5
3 | 6
4 | 4
5 | 4

Sau khi hệ thống gỡ bỏ Cloud Server 3:

![VM_Node_Remove_Cloud_Server_After](./images/VM_Node_Remove_Cloud_Server_After.png)

Cloud\_Server | Virtual\_Node\_Number
--------------|----------------------
1 | 7
2 | 6
4 | 6
5 | 5

Tương tự như trong trường hợp thêm mới một Cloud Server, trước khi gỡ bỏ Cloud Server cũ, chúng ta cần di chuyển các Replica từ Cloud Server cũ sang các Cloud Server mà Virtual Server ánh xạ tới trong trạng thái mới.

### 3.4 Quản lý thông tin tài khoản người dùng và danh sách các Data Object trong tài khoản người dùng đang thực hiện thay đổi

Trong mô hình VM Ring, để lưu trữ thông tin người dùng và các Data Object đang thực hiện thay đổi trên hệ thống, chúng ta sử dụng một trong các phương án sau:

- Lưu trữ các thông tin này trong cơ sở dữ liệu (tương tự như trong mô hình Store Mapping by Database)
- Tạo một VM Ring riêng biệt chỉ dùng để lưu trữ thông tin về tài khoảng người dùng và danh sách các Data Object đang thực hiện thay đổi. Thông tin của người dùng được lưu trữ trên các VM này (tạo AccountID bằng cách Hashing AccountName).Trong mô hình VM Ring, do hệ thống phục vụ cho nhiều người dùng, mỗi người dùng sở hữu một danh sách các Cloud Server độc lập với nhau, do đó mỗi người dùng hệ thống sẽ được hệ thống tạo cho một VM Ring riêng, và VM Ring đó chỉ phục vụ cho người dùng này. VM Ring sử dụng để lưu trữ thông tin về các tài khoản người dùng và danh sách các Data Object đang thay đổi là một VM độc lập, do hệ thống MCS tạo ra và phục vụ cho hệ thống MCS.

## 4. Mô hình Cloud Ring with Reference Node

Mô hình Cloud Ring with Reference Node cũng được xây dựng dựa trên nền tảng Chord Protocol, tuy nhiên Ring lúc này nằm bên trong MCS API Server, các Node trên Chord Logic Ring lúc này sẽ là các đối tượng tồn tại bên trong API Server Process.

Khi sử dụng mô hình này, thông tin chứa trên các Node đơn thuần là địa chỉ của các Cloud Server đang chứa các Replica của Object này.

Quá trình lookup cơ bản Data Object khi hệ thống sử dụng mô hình Reference Node diễn ra như sau:

Client sẽ gửi yêu cầu tải về một Data Object có tên tuyệt đối là **x** lên MCS API Server. MCS API Server nhận được request sẽ thực hiện việc tạo **Data\_Object\_ID = Hashing(Data\_Object\_Name)** rồi thực hiện phương thức lookup từ một trong các Node trên Ring. Reference Node sẽ dựa vào Chord Lookup Protocol để đi tới Reference Node là Successor Node của **Data\_Object\_ID** này, Cloud Server được Reference Node này đại diện cho chính là Cloud Server chứa Data Object cần tìm. Lúc này, Reference Node sẽ trả về cho MCS API Server thông tin của Cloud Server mà nó đang đại diện. MCS API Server gửi thông tin này tới Client, sau đó Client sử dụng thông tin này để kết nối trực tiếp tới Cloud Server để tải về nội dung của Data Object.

![Virtual_Node_Architech](./images/HA_current_architect.png)

### 4.1 Xây dựng cơ chế giải quyết các vấn đề phân phối đồng đều dữ liệu theo dung lượng Cloud Server và sao lưu Data Object

Về cơ bản, các đặc điểm của cơ chế xử lý vấn đề phân phối dữ liệu và sao lưu Data Object của mô hình Reference Node giống với mô hình VM node. Sự khác biệt chủ yếu của hai mô hình là, Node trong mô hình Reference Node là các đối tượng nằm trong một Process, còn Node trong mô hình VM node là các máy ảo - Virtual Machine.

Vì vậy, giải pháp để giải quyết vấn đề phân phối dữ liệu lưu trữ lên các Cloud Server và sao lưu Data Object và ở 2 mô hình là tương tự nhau: Giải pháp sử dụng Virtual Server kết hợp với phương pháp cân bằng giữa Dung lượng lưu trữ với số lượng Virtual Server của một Cloud Server. Triển khai cụ thể của giải pháp này trong mô hình Reference Node là:

1. Xác định số lượng Reference Node có trên Ring: m.
1. Xác định số lượng Bản sao - Replica của một Data Object: k.
1. Với mỗi một Reference Node trên Ring, tạo ra k Virtual Server trên Reference Node đó. Sau đó, xác định k Virtual Server này ánh xạ tới k Cloud Server phân biệt nào theo một thuật toán phân phối và dựa trên các thông tin sau:
    - Số lượng các Virtual Server đã ánh xạ tới từng Cloud Server.
    - Dung lượng (weight) của từng Cloud Server.

Sau khi xác định được giá trị các Virtual Server trên các Node, bước tiếp theo chúng ta cần thực hiện là Tạo ra Cloud Ring từ các Reference Node, sau đó chuyển Cloud Ring tới tất cả các thực thể (process) có sử dụng Ring để tương tác với Data Object.

![Reference_Ring_Virtual_Cloud](./images/Reference_Ring_Virtual_Cloud.png)

Đi kèm với mỗi Ring là một danh sách các Cloud Server cung cấp thông tin truy cập tới Cloud Server

CloudID | Type | Access\_Data
--------|------|-------------
1 | Amazon\_S3 | User:x1 - Password:x1\_pass
2 | Swift | User:x2 - Password:x2\_pass - ServerIP:x2\_IP
3 | Swift | User:x3 - Password:x3\_pass - ServerIP:x3\_IP
4 | Swift | User:x4 - Password:x4\_pass - ServerIP:x4\_IP
5 | Amazon\_S3 | User:x5 - Password:x5\_pass
6 | Swift | User:x6 - Password:x6\_pass - ServerIP:x6\_IP

### 4.2 Phương thức lưu trữ và truy cập trạng thái của Data Object và của các Replica

Trong mô hình Reference Node, các Node chỉ là các đối tượng tồn tại trong các process, do đó khác mô hình VM node, chúng ta không thể lưu trữ trạng thái của các Replica và của Data Object trên VM node.

Giải pháp để lưu trữ các thông tin này, đó là sử dụng metadata của các Object lưu trữ trên các Cloud Server. Khi một Object được lưu trữ trên các Cloud Server, thì chúng ta có thể lưu cùng với Object đó các thông tin liên quan tới Object, các thông tin đó được gọi là Object Metadata ( chính vì vậy, nên các Drive trong hệ thống Swift được format dưới định dạng XFS). Trong hệ thống của chúng ta, các Replica của một Data Object được lưu trữ dưới dạng một Object trong Cloud Server, do đó trạng thái của Replica đó có thể được lưu trữ như Object Metadata trên Cloud Server. Còn trạng thái của một Object có thể được lưu trữ theo 2 cách sau:

- Hoặc chúng ta lấy về tất cả các trạng thái của các Replica của một Data Object rồi suy ra trạng thái của Data Object từ trạng thái của các Replica của nó.
- Hoặc chúng ta sao lưu trạng thái của Data Object đó ra k lần và lưu mỗi một bản sao thành một Metadata của một Replica. Trong trường hợp này, metadata của một replica chứa 2 thông tin: Trạng thái của Replica đó, và trạng thái của Data Object.

![Replica_Metadata.png](./images/Replica_Metadata.png)

Trong mô hình Reference Node, quá trình Lookup đầy đủ diễn ra như sau:

Với mô hình này, quá trình Lookup trong hệ thống diễn ra như sau:

1. Client của người dùng gửi Request tới MCS API Server.

1. MCS API Server hashing tên của Data Object người dùng muốn lấy về => lấy được **ObjectID**, sau đó nó sử dụng Cloud Ring để tìm ra Successor Node của **ObjectID** này.
1. MCS API Server lấy thông tin tương ứng với Reference Node là Successor Node của **ObjectID** để xác định các Replica của Data Object này đang nằm trên các Cloud Server nào. Sau đó, MCS API Server truy cập vào các Cloud Server này để lấy ra các Metadata của các Replica.
1. Sau khi MCS API Server lấy được Metadata của các Replica của Data Object đó, dựa vào trạng thái của các Replica và trạng thái của Data Object, MCS API Server xác định Data Object mà người dùng muốn truy cập có ở trong một trong các trạng thái hợp lệ hay không. Nếu điều này thỏa mãn,MCS API Server sẽ lấy ra thông tin truy cập một Replica của Data Object đó đang ở trạng thái UPDATED rồi trả thông tin này về cho Client.
1. Client sử dụng thông tin truy cập mà MCS API Server trả về để kết nối trực tiếp với Cloud Server để lấy về nội dung của Data Object.

### 4.3 Phương thức thêm mới, gỡ bỏ một Cloud Server khỏi hệ thống

Phương thức thêm mới và gỡ bở Cloud Server khỏi hệ thống trong mô hình Reference Node tương tự như phương thức xử lý trong mô hình VM Ring. Phương thức cụ thể như sau:

#### 4.3.1 Thêm mới một Cloud Server

Khi thêm mới một Cloud Server vào hệ thống, chúng ta sẽ tạo ra một ring mới cho hệ thống. Ring mới được tạo ra dựa vào các thông tin sau:

- Thông tin về Ring hiện tại trong hệ thống.
- Thông tin về Cloud Server mới sẽ được thêm vào hệ thống.
- Phương thức phân phối được sử dụng.

Ví dụ về quá trình tạo ra Cloud Ring mới khi thêm một Cloud Server vào hệ thống:

Trước khi người dùng thêm Cloud Server 7, Cloud Ring của người dùng có sơ đồ như sau:

![VM_Node_Add_Cloud_Server_Before](./images/Reference_Node_Before.png)

Trước khi thay đổi, ta có số lượng Virtual Server ánh xạ tới các Cloud Server là:

Cloud\_Server | Virtual\_Node\_Number
--------------|----------------------
1 | 4
2 | 3
3 | 4
4 | 6
5 | 5
6 | 2

Sau khi thêm Cloud Server 7 vào hệ thống, chúng ta thực hiện thay đổi ánh xạ trên một số Virtual Server trong một số VM để chuyển Virtual Server đó ánh xạ sang Cloud Server 7. Các Virtual Server sẽ thay đổi ánh xạ được lựa chọn theo một trong các phương pháp phân phối như Round Robin, most Used...:

![VM_Node_Add_Cloud_Server_After](./images/Reference_Node_After.png)

Cloud\_Server | Virtual\_Node\_Number
--------------|----------------------
1 | 4
2 | 3
3 | 3
4 | 4
5 | 4
6 | 2
7 | 4

Sau khi tạo ra Ring mới, chúng ta tiến hành chuyển Ring mới này tới tất cả các thực thể (Process) sử dụng Ring này để tương tác với các Data Object của người dùng, sau đó thực hiện việc di chuyển các Replica từ Cloud Server cũ sang Cloud Server mới

#### 4.3.2 Gỡ bỏ một Cloud Server

Để gỡ bỏ một Cloud Server khỏi hệ thống, chúng ta cũng thực hiện công việc rebalancing với một phương pháp phân phối xác định tương tự như trong trường hợp thêm mới Cloud Server.

Ví dụ, trước khi hệ thống gỡ bỏ Cloud Server 6:

![VM_Node_Add_Cloud_Server_Before](./images/Reference_Node_Before.png)

Cloud\_Server | Virtual\_Node\_Number
--------------|----------------------
1 | 4
2 | 3
3 | 4
4 | 6
5 | 5
6 | 2

Sau khi hệ thống gỡ bỏ Cloud Server 6:

![VM_Node_Remove_Cloud_Server_After](./images/Reference_Node_Remove_After.png)

Cloud\_Server | Virtual\_Node\_Number
--------------|----------------------
1 | 4
2 | 4
3 | 5
4 | 6
5 | 5

Tương tự như trong trường hợp thêm mới một Cloud Server, sau khi Ring mới được tạo ra, chúng ta phải chuyển Ring mới tới các thực thể tương tác với Data Object, cũng như di chuyển các Replica từ Cloud Server cũ sang các Cloud Server mới.

### 4.4 Quản lý thông tin tài khoản người dùng và danh sách các Data Object trong tài khoản người dùng đang thực hiện thay đổi

Trong mô hình Reference Node, để lưu trữ thông tin người dùng và các Data Object đang thực hiện thay đổi trên hệ thống, chúng ta sẽ sử dụng backend là MCS Ring - Cloud Ring riêng biệt như phương án 2 trong mô hình VM Ring. Theo đó, thông tin của người dùng cũng như các danh sách chứa các Data Object đang được thay đổi sẽ được lưu trữ trên các trên Cloud Server trên MCS Ring thay vì trên Database chung.

Do vậy, khi sử dụng mô hình Reference Node, trên một thực thể sẽ chứa (**N+1**) Ring, trong đó N là số lượng người dùng hệ thống, cộng thêm một MCS Ring của bản thân hệ thống:

![reference_ring_overal_architect](./images/reference_ring_overal_architect.png)

## 5. Phân tích và so sánh đặc điểm của các mô hình

Sau khi đã tiến hành khảo sát, phân tích đặc điểm và xây dựng các cơ chế xử lý quan trọng nhất cho 3 mô hình trên, chúng ta đi vào phân tích so sánh 3 mô hình với nhau để đánh giá các điểm mạnh và điểm yếu của từng mô hình, sau đó lựa chọn ra mô hình phù hợp nhất.

Các tiêu chí được đưa ra để đánh giá là: Hiệu năng của hệ thống và các điểm nghẽn trong mô hình, khả năng scaling - tài nguyên sử dụng để triển khai mô hình, khả năng chống lỗi và phục hồi. Tất cả các so sánh được đặt trên giả thiết là hệ thống được triển khai trên quy mô lớn.

### 5.1 Đánh giá hiệu năng hệ thống và các điểm tắc nghẽn trong mô hình

- Với mô hình Store Mapping by Database: Ở quy mô hệ thống nhỏ, hiệu năng của mô hình này là chấp nhận được, thậm chí trong một số thao tác như kiểm tra trạng thái của Data Object và của các Replica, và truy cập vào thông tin tài khoản User , mô hình này sẽ cho tốc độ cao nhất trong 3 mô hình. Tuy nhiên khi hệ thống có quy mô lớn, hệ thống này tồn tại một điểm tắc nghẽn lớn, đó là Database. Khi nhu cầu hệ thống tăng mạnh, thành phần Database sẽ trở nên quá tải và làm giảm mạnh hiệu năng của hệ thống.
- Với mô hình VM Ring, tốc độ thực thi trong hệ thống có quy mô lớn là chấp nhận được. Tuy nhiên thao tác Lookup Data Object sẽ có độ trễ lớn, do các Node trao đổi với nhau thông qua HTTP request có độ trễ lớn, và theo Chord Protocol, thì hệ thống cần đi qua O(log N) node để tìm được Successor node, do đó chúng ta cần thực hiện lần lượt O(log N) HTTP request để hoàn thành thao tác lookup. Tuy nhiên, có một nguy cơ tắc nghẽn trong hệ thống sử dụng mô hình này, đó là nguy cơ tắc nghẽn hệ thống mạng khi số lượng thao tác Lookup trên hệ thống là lớn.
- Với mô hình Reference Node, tốc độ các thao tác tương tác với Ring là rất tốt ngay cả khi hệ thống có quy mô lớn, do các Ring sử dụng để Lookup đều nằm trong bộ nhớ RAM. Đồng thời, tương tự như mô hình VM Ring, mô hình này hầu như không tồn tại điểm tắc nghẽn. Một điểm yếu của mô hình này, đó là để lấy được trạng thái của Data Object, mô hình này có thể phải truy cập tới tất cả các Cloud Server chứa Replica của Data Object đó.

Chúng ta sẽ đánh giá cụ thể hiệu năng cũng như tải đặt lên các thành phần trong hệ thống với 3 mô hình trên trong trường hợp hệ thống hoạt động thực tế. Để công bằng, cả 3 mô hình sẽ đều có **X1** API Server. Ngoài ra, với từng mô hình sử dụng các thành phần, đối tượng và cách phối hợp khác nhau, do vậy số lượng các thành phần khác trong hệ thống ( như database server, VM Node, ...) có thể khác nhau, tuy nhiên sự biệt này gây ra bởi thiết kế của mô hình mà hệ thống sử dụng, do vậy sự khác biệt này không ảnh hưởng tới sự công bằng của đánh giá.

Thử nghiệm được thực hiện là: **N** request truy cập các Data Object được gửi tới hệ thống trong một đơn vị thời gian. Hiệu năng của một hệ thống được đánh giá thông qua thời gian trung bình để một API server phục vụ xong - phản hồi một request. Yếu tố quan trọng nhất trong các yêu tố ảnh hưởng tới thời gian để API phục vụ xong một request, đó là thời gian cần thiết để một API Server lấy được 3 thông tin của Data Object **(\*)**: vị trí của các replica của một Data Object, và trạng thái của Data Object đó cũng như trạng thái của các Replica của Data Object đó.

Với hệ thống sử dụng mô hình Store Mapping by Database, hệ thống sẽ chỉ có 1 Database. Để lấy được thông tin **(\*)**, API Server cần gửi một HTTP request tới Database để lấy về thông tin của một Data Object. Thời gian để API Server lấy được **(\*)** là:

> **T1** = thời gian trung bình mà database xử lý xong một request.

Tuy nhiên, với thử nghiệm này, trong một đơn vị thời gian, Database phải xử lý **N** HTTP request - cũng có nghĩa là lượng tải lớn nhất trong hệ thống được đặt lên duy nhất database, do vậy thời gian trung bình mà database cần để xử lý xong một request là không nhỏ.

Với hệ thống sử dụng mô hình VM Ring có  **X1** API Server và **X2** VM node, để lấy được thông tin **(\*)**, API server sẽ gửi yêu cầu phân giải tới một VM node. Yêu cầu phân giải phải đi qua O(log **X2** ) HTTP request để đi được tới VM node chứa (\*). Như vậy, trong mô hình này, thời gian để API Server lấy được **(\*)** là:

> **T2** = O(log **X2** ) x (thời gian Chord Protocol trên các VM Node xử lý điều hướng phân giải + thời gian truyền một HTTP request giữa 2 VM Node) + thời gian succesor VM node xử lý yêu cầu phân giải.

**X2** ở đây cần được tính toán hợp lý. Bởi vì, nếu **X2** quá lớn thì thời gian xử lý phân giải lớn (do hệ số O(log **X2** ) trong công thức tính **T2**. Còn nếu **X2** quá nhỏ, thì các VM node sẽ phải chịu lượng tải lớn, cũng như tính cân bằng của hệ thống bị yếu đi, vì như chúng ta thấy trong thử nghiệm này, trong 1 đơn vị thời gian 1 VM node cần xử lý **N/X2** yêu cầu phân giải.

Với hệ thống sử dụng Reference Node có **X1** API Server, **X2** Reference Node và **X3** Cloud Server. để lấy được thông tin **(\*)**, API server cần đi qua O(log **X2** ) Reference Node để lấy được thông tin về vị trí của các Object Replica. Sau đó, để lấy được Object Metadata và Replica Metadata, API Server cần gửi **k** HTTP request xuống các Cloud Server, với k là hệ số Replica của Data Object. Như vậy, thời gian để API Server lấy được **(\*)** trong mô hình này là:

> **T3** = O(log **X2** ) x (thời gian di chuyển giữa các Reference Node trong bộ nhớ RAM)b + (thời gian cả k Cloud Server xử lý xong k HTTP request truy cập Object Metadata và Replica Metadata của API Server).

Chúng ta cần lưu ý ba đặc điểm khi phân tích mô hình Reference Node, đó là: Thứ nhất, thời gian di chuyển giữa các Reference Node là rất nhanh, do các Reference Node thực tế là các Object nằm trên bộ nhớ trong - RAM của API Server. Thứ hai,  k HTTP request trong công thức tính **T3** có thể thực hiện song song, chứ không cần phải thực hiện tuần tự như các HTTP request trong công thức tính **T2**. Thứ 2, để hệ thống đáp ứng **N** request trong một đơn vị thời gian, các API Server trên hẹ thống sẽ gửi đi **k**x**N** HTTP request xuống các Cloud Server để lấy Object Metadata và Replica Metadata, do đó trong một đơn vị thời gian một Cloud Server sẽ phải xử lý trung bình (**k**x**N**)/**X3** HTTP request. Điều này cũng có nghĩa rằng, số Cloud Server càng lớn thì tải đặt lên một Cloud Server càng nhỏ.

Qua phân tích thử nghiệm trên, chúng ta có thể thấy rằng mô hình Reference Node là mô hình cho hiệu năng tốt nhất, trong trường hợp thời gian một Cloud Server xử lý một yêu cầu truy cập Object Metadata và Replica Metadata là chấp nhận được. Mô hình VM Ring đạt yêu cầu về hiệu năng, tuy rằng thời gian để VM Ring tìm ra successor VM node là khá lớn, do các HTTP request phải được xử lý tuần tự. Mô hình Store Mapping by Database sẽ không đạt yêu cầu về hiệu năng trong hệ thống quy mô lớn, và trong mô hình này có điểm tắc nghẽn lớn - tải đặt lên thành phần database là tuyến tính với số lượng request.

### 5.2 Khả năng Scaling và tài nguyên sử dụng cho từng mô hình

Tiếp tục phân tích thử nghiệm mà chúng ta vừa thực hiện, chúng ta có thể thấy rằng:

- Mô hình Store Mapping by Database không có khả năng Scaling trên quy mô lớn, do đặc điểm điểm nghẽn Database không thể Scaling được. Tài nguyên mà mô hình Store Mapping by Database sử dụng là không lớn, tuy nhiên điều này không có nhiều ý nghĩa khi hệ thống không thể scaling được.
- Với đặc điểm không có điểm tắc nghẽn lớn, mô hình VM Ring có thể Scaling trong một dải phạm vi lớn. Tuy nhiên khi hệ thống mở rộng ở quy mô lớn, lượng tài nguyên tiêu thụ để triển khai mô hình này là lớn nhất trong 3 mô hình. Vì đơn giản là khi hệ thống cần phục vụ cho N User, mỗi một Ring cho một User cần M - VM máy ảo, thì khi đó số lượng máy ảo cần tạo ra để triển khai mô hình này là N*M. Mà tài nguyên sử dụng của một máy ảo không hề thấp. Khi hệ thống triển khai trên quy mô lớn, số lượng User lên tới hàng trăm User, chúng ta thậm chí phải triển khai tới hàng trăm, hàng nghìn VM để phục vụ mô hình.
- Với mô hình Reference Node, chi phí, chi phí để quản lý Ring cho một User chỉ là bộ nhớ mà Ring đó chiếm giữ trên Process. Chi phí này là nhỏ hơn nhiều so với Chi phí bỏ ra để triển khai máy ảo trong mô hình VM Ring. Một điểm yếu nhỏ trong mô hình này, đó là mọi thực thể trong hệ thống đều cần phải có một bản sao hệ thống Ring bên trong bộ nhớ. Điểm yếu này có thể khắc phục bằng các triển khai các Process phục vụ riêng cho thao tác Lookup, và các Process khác có nhu cầu sử dụng Ring sẽ gửi Request tới các Process này, như vậy sẽ giảm bớt số lượng bản sao của hệ thống Ring phải tạo ra. Lượng tài nguyên tiêu thụ trong mô hình này so với mô hình VM Ring là nhỏ hơn rất nhiều. Tương tự như mô hình VM Ring, hệ thống này không có điểm tắc nghẽn lớn, cộng với việc tài nguyên sử dụng là nhỏ, do đó khả năng Scaling của mô hình này là tốt nhất trong 3 mô hình.

Kết luận với tiêu chí thứ 2: Mô hình Reference Node là mô hình có khả năng scaling tốt nhất, cũng như lượng tài nguyên tiêu thụ nằm trong phạm vi hệ thống có thể cung cấp. Mô hình VM Ring đòi hỏi lượng tài nguyên tiêu thụ rất lớn, trong khi đó mô hình Store Mapping by Database không có khả năng Scaling trên quy mô lớn.

### 5.3 Khả năng chống lỗi và phục hồi

Vẫn như 2 tiêu chí trước đó, bottleneck ở Database khiến cho mô hình Store Mapping by Database có khả năng chống lỗi kém - Single Node Failure. Về khả năng phục hồi, tuy chúng ta có thể sử dụng giải pháp backup Database, tuy nhiên trong một số trường hợp nếu như chúng ta không backup kịp thời và thường xuyên, một số dữ liệu trong Database sẽ bị mất mát.

Với mô hình VM Ring, khả năng chống lỗi của mô hình này là tốt hơn so với mô hình Store Mapping by Database, do khi một VM nào đó trên Ring bị hỏng, thì Ring vẫn hoạt động. Tuy nhiên, điểm yếu của mô hình này là khi một VM bị hỏng, thì các dữ liệu, cũng như các Data VM trên Ring đó sẽ bị mất. Một số giải pháp để khắc phục vấn đề này, đó là Backup dữ liệu trên VM, hoặc cho phép 2 VM cùng tham chiếu tới một node. Tuy nhiên, về bản chất tự nhiên, thì mô hình này không có khả năng chống lỗi hoàn toàn.

Với mô hình Reference Node, do hàng loạt bản sao được tạo ra trên các thực thể (Process), cũng như do tất cả mọi thông tin đều được sao lưu nhiều lần, nên về thực tế mô hình này có khả năng chống lỗi rất tốt. Khi một Process bị hỏng, hoặc thậm chí một Cloud Server bị hỏng, thì các thông tin sao lưu cũng như thông tin về các Ring vẫn được sao lưu ở các nơi khác, do vậy, các thông tin trong hệ thống luôn có hệ số an toàn cao, cũng như hệ thống có khả năng phục hồi khi sự cố xảy ra.

Như vậy, trong tiêu chí thứ 3, độ ổn định và khả năng chống lỗi của hệ thống của mô hình Reference Node vẫn là tốt nhất. Mô hình VM Ring cũng có khả năng chống lỗi, tuy nhiên khi sử dụng mô hình này, vẫn có khả năng xảy ra mất mát thông tin khi hệ thống gặ sự cố  nếu không triển khai các biện pháp khác. Mô hình Store Mapping by Database không có khả năng chống lỗi tốt.

## 5. Lựa chọn mô hình cơ sở để phát triển hệ thống MCS

Như vậy, thông qua các phân tích và các so sánh, chúng ta có thể thấy trong 3 mô hình được đưa ra, mô hình Reference Node là mô hình tốt nhất để làm cơ sở phát triển hệ thống MCS. Tất nhiên, trong hệ thống MCS, ngoài các vấn đề nêu ra trong bài viết, sẽ còn rất nhiều vấn đề cần phải giải quyết bằng các cơ chế xử lý khác, tuy nhiên, trên cơ sở những gì đã phân tích, chúng ta có thể thấy mô hình Reference Node có thể giải quyết được các vấn đề quan trọng nhất trong hệ thống MCS. Vì vậy, chúng ta có thể sử dụng mô hình Reference Node để làm nền tảng phát triển hệ thống tích hợp Cloud Server MCS.

## Tài liệu tham khảo