# CONFIGURATION FOR OBJECT STORAGE SERVICE WHICH WILL BE MANAGED BY THIS
# MCOS SERVICE
TEST_CONTAINER_NAME = 'mcos.test.container'
TEST_OBJECT_NAME = 'mcos_test_object'
TEST_FILE_PATH = './mcos/media/configs/sample_file.txt'

STORAGE_CONTAINER_NAME = 'mcos_storage_container_name'
STORAGE_SERVICE_CONFIG = {
    "type": "swift",  # valid type: amazon_s3, swift, ceph
    # 'access_info': {
    #     'ip': '192.168.122.100',
    #     'port': '8080',
    # },
    "auth_info": {
        'os_auth_url': 'http://192.168.122.100:35357/v3',
        'os_project_name': 'admin',
        'os_username': 'admin',
        'os_password': 'bkcloud',
        'os_project_domain_name': 'Default',
        'os_user_domain_name': 'Default',
        'os_identity_api_version': '3',
        'os_auth_version': '3',
        'os_swiftclient_version': '2.0',
    },
    "specifications": { # hdd large
        "capacity": "30000",  # in TB
        "backend-type": "SSD",  # HDD, SSD, None
        "128k-read": "90",
        "128k-write": "60",
        "10mb-read": "600",
        "10mb-write": "300",
    }
    # "specifications": { # ssd_small
    #     "capacity": "500",  # in TB
    #     "backend-type": "HDD",  # HDD, SSD, None
    #     "128k-read": "60",
    #     "128k-write": "30",
    #     "10mb-read": "300",
    #     "10mb-write": "200",
    # }
    # "specifications": { # hdd_small
    #     "capacity": "1000",  # in TB
    #     "backend-type": "HDD",  # HDD, SSD, None
    #     "128k-read": "9",
    #     "128k-write": "6",
    #     "10mb-read": "60",
    #     "10mb-write": "30",
    # }
}

# # EXAMPLE CONFIG FOR SWIFT
# OBJECT_STORAGE_SERVICE_CONFIG = {
#     "type": "swift",
#     "address": "192.168.47.110",
#     "port":"8000",
#     "os_auth_url": "http://192.168.47.110:5000/v3",
#     "os_project_name": "admin",
#     "os_username": "admin",
#     "os_password": "admin@123",
#     "os_project_domain_name": "default",
#     "os_identity_api_version": "3",
#     "os_auth_version": "3",
#     "os_image_api_version": "2",
#     "os_novaclient_version": "2.1",
#     "os_swiftclient_version": "2.0"
# }
#
# # EXAMPLE CONFIG FOR S3
#
# OBJECT_STORAGE_SERVICE_CONFIG = {
#     "type": "amazon_s3",
#     "address": "192.168.47.201",
#     "aws_access_key_id": "sdasd123123",
#     "aws_secret_access_key": "12asdasdad",
#     "region_name": "RegionOne",
#     "endpoint_url": "http://192.168.47.201:8778"
# }
