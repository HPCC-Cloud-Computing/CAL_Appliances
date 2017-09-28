# MCOS Note And Issue

## CAL Library

Các giá trị trả về của một số phương thức liên quan tới object storage trong CAL:

- Phương thức ```create_container``` - kết quả trả về như thế nào nếu:
    - Trường hợp 1: Nếu container chưa tồn tại.
    - Trường hợp 2: Nếu container đã tồn tại.
    
- Phương thức ```upload_container``` - kết quả trả về:
    - Nếu hợp lệ, phương thức này sẽ chờ cho tới khi việc upload và save hoàn tất mới chuyển tới lệnh tiếp theo -> phương thức này thực hiện theo cơ chế đồng bộ - synchronous - lưu ý quan trọng cho việc phát triển CAL.
    - Nếu không hợp lệ (ví dụ kích thước file quá to), phương thức này raise ra 1 exception.
    - Nếu file được upload đã tồn tại, thì CAL ghi đè vào file hiện tại (đã kiểm tra). Tuy nhiên nếu dùng horizon upload thì horizon lại không cho phép ghi đè vào file mà thông báo cho người dùng là file đã tồn tại ????
    - Đã thử nghiệm với swift client, swift client cũng ghi đè như CAL, như vậy là do horizon không cho ghi đè chứ không phải là swift client không cho ghi đè.
    - Trong trường hợp 2 người dùng khác nhau đồng thời cùng upload một file cùng tên lên server, hệ thống sẽ phản ứng ra sao ?
    - Công việc cần làm: 
        - Sử dụng Swift Client để kết nối thử nghiệm.

        - Sử dụng OpenVSwitch để tạo switch nhằm mục đích điều khiển băng thông tới các con máy ảo cài Swift và Amazon S3