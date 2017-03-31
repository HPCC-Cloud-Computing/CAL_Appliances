 *Chú ý, các từ khóa sử dụng bên dưới:*

| Từ khóa        | Chú thích         | 
| ------------- |:-------------:|
| người dùng     | Bấy kỳ người nào có các tài khoản của nhiều providers, sử dụng ứng dụng web này để quản lý apps như một developer chẳng hạn. |
| providers      | Các nhà cung cấp cloud hoặc các cụm private cloud     |
|apps| Là các ứng dụng mà người dùng(developer) triển khai vào cloud|

### Tính năng mong đợi
- Quản lý cloud providers
	+ Thêm, liệt kê, sửa và xóa
	+ Validate lại providers(connection, ...)
- Quản lý network
	+ Thêm, liệt kê, sửa và xóa
	+ Validate lại quota và commitment
- Quản lý apps 
	+ Thêm, liệt kê, sửa và xóa
	+ Kết nối giữa các apps
	+ Migrate
	+ Snapshot(checkpoint container)
	
### Phân tích công nghệ sử dụng

Với yêu cầu như trên, chúng ta có thể xây dựng webapp sử dụng Django framework và nhúng callib vào. Với từng tính năng cụ thể, chúng ta cùng phân tích các yêu cầu về công nghệ:

- <b>Quản lý cloud providers</b>
	+ Thêm, liệt kê, sửa và xóa: là các thao tác cơ bản, sử dụng cơ sở dữ liệu mysql để lưu trữ
	+ Validate providers: đây là bước để người dùng kiểm tra lại một providers có đúng như mình mong muốn. Về bản chất, trong callib là một hàm abstraction, vì vậy, ứng dụng này đơn giản là overwrite lại hàm đó

- <b>Quản lý network </b>
	+ Thêm, liệt kê, sửa và xóa: tương tự trên
	+ Validate lại quota và commitment:
		+ Với quota: Để giảm thiểu việc các request về các providers không được chấp thuận, chúng ta có thể check quota của các providers dành cho từng người dùng trên cloud của providers đó. Quota ở đây đã được xây dựng sẵn như là các class ở trong callib.
		+ Với commitment: Chúng ta phải overwrite lại hàm validate về commitment trong callib - cái mà nhóm phát triển callib đã dựng sẵn một hàm abstraction.

- <b>Quản lý apps </b>

	+ Thêm, liệt kê, sửa và xóa: 
		+ Thêm: Sử dụng callib để khởi tạo các máy ảo có sẵn docker engine, thực hiện deploy các ứng dụng trên đó qua docker images. Để đảm bảo việc kết nối từ bên ngoài và không bị trùng port bên trong cũng như trong suốt việc app = máy ảo + containers, chúng ta sẽ chỉ tạo một container trong một máy ảo và trong suốt với người dùng như đó là một app của họ.
		+  Liệt kê: liệt kê các ứng dụng và tương ứng máy ảo nào đang chứa nó
		+ Sửa: Cập nhật version của ứng dụng qua tag của docker images, sửa tên ứng dụng...
		+ Xóa: xóa máy ảo
		
	+ Kết nối giữa các apps:
		+ kết nối giữa apps được đảm bảo bởi phần quản lý network, tạo ra các mạng và chỉ việc thêm apps vào mạng đó là có thể kết nối
		+ người dùng buộc phải khai bảo các port được phép truy cập từ bên ngoài tới apps để đảm bảo tính bảo mật và được cấu hình thông qua callib - security groups

	+ Migrate: #TODO
	+ Snapshot: #TODO

Tóm tắt:

	- Django +  HTML + CSS : xây dựng  giao diện web
	- MYSQL :  Lưu trữ providers, các metadata cho các máy ảo, apps,...
	- callib: Một thư viện cloud abstract layer
	- 
	
### Phân tích giao diện
	# TODO