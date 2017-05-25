from base import *

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'mcs',
        'HOST': '172.17.0.2',
        'USER': 'root',
        'PASSWORD': 'secret',
        'PORT': 3306
    }
}

CELERY_BROKER_URL = 'redis://192.168.122.10:6379/0'
CELERY_RESULT_BACKEND = 'redis://192.168.122.10:6379/1'
CELERY_ACCEPT_CONTENT = ['application/x-python-serialize']
CELERY_TASK_SERIALIZER = 'pickle'
CELERY_RESULT_SERIALIZER = 'pickle'
CELERY_TIMEZONE = 'Asia/Ho_Chi_Minh'

MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'
