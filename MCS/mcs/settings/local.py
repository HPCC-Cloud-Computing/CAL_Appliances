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

CELERY_BROKER_URL = 'redis://redis:secret@172.17.0.3:6379'
CELERY_RESULT_BACKEND = 'redis://redis:secret@172.17.0.3:6379'
CELERY_ACCEPT_CONTENT = ['application/x-python-serialize']
CELERY_TASK_SERIALIZER = 'pickle'
CELERY_RESULT_SERIALIZER = 'pickle'
CELERY_TIMEZONE = 'Asia/Ho_Chi_Minh'

MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'
