from base import *

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'mcos',
        'HOST': '127.0.0.1',
        'USER': 'root',
        'PASSWORD': 'bkcloud',
        'PORT': 3306
    }
}

KEYSTONE_AUTH_URL = "http://172.20.4.1:5000/v3"
KEYSTONE_USER_DOMAIN_ID = 'default'
KEYSTONE_PROJECT_DOMAIN_NAME = 'default'
KEYSTONE_PROJECT = 'mcos'
KEYSTONE_ADMIN_USERNAME = 'admin'
KEYSTONE_ADMIN_PASSWORD = 'bkcloud'


CELERY_BROKER_URL = 'redis://127.0.0.1:6379/0'
CELERY_RESULT_BACKEND = 'redis://127.0.0.1:6379/1'
CELERY_ACCEPT_CONTENT = ['application/x-python-serialize']
CELERY_TASK_SERIALIZER = 'pickle'
CELERY_RESULT_SERIALIZER = 'pickle'
CELERY_TIMEZONE = 'Asia/Ho_Chi_Minh'
