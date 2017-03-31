### Cấu trúc các bảng dữ liệu của fcap trong cơ sở dữ liệu fcap

- Bảng dữ liệu dành cho login của người dùng nắm giữ các provider: Sử dụng bảng xác thực có sẵn User của Django, tuy nhiên chỉ sử dụng các trường sau:
```
user(id, name, password, first_name, last_name)
```
- Bảng dữ liệu cho các providers mà người dùng cung cấp:
```
provider(id, name, config, description, enable, type, user_id)
```
Với setup trong Django model như sau:
```
    name = models.CharField(max_length=50)
    config = models.TextField()
    description = models.TextField()
    enable = models.PositiveSmallIntegerField(default=0)
    type = models.TextField()
    user = models.ForeignKey(User, on_delete=models.CASCADE)
```
Ở đây, user_id là foreign key , reference tới bảng user ở trên

- Bảng dữ liệu chứ các network mà người dùng tạo trên các cloud:

```
network(id, name, description, network_id, cidr, gateway, security_group, allocation_pools, dns_nameservers, connect_external, provider_id)
```
Và setup trong Django model như sau:

```
    name = models.CharField(max_length=100)
    description = models.TextField()
    network_id = models.TextField()
    cidr = models.TextField()
    cloud = models.TextField()
    gateway = models.TextField()
    security_group = models.TextField()
    allocation_pools = models.TextField()
    dns_nameservers = models.TextField()
    connect_external = models.PositiveSmallIntegerField(default=0)
    provider = models.ForeignKey(Provider, on_delete=models.CASCADE)
    
```
 
- Bảng dữ liệu chứ các apps mà người dùng tạo trên các cloud:

```
app(id, name, description, instance_id, network_id, docker_image, ports, ip, start_script, state, provider_id)

```

Và setup trong Django model như sau:

```
    name = models.CharField(max_length=100)
    description = models.TextField()
    instance_id = models.TextField()
    network_id = models.TextField()
    docker_image = models.TextField()
    ports = models.TextField()
    ip = models.TextField()
    start_script = models.TextField()
    state = models.TextField()
    provider = models.ForeignKey(Provider, on_delete=models.CASCADE)
    
```
