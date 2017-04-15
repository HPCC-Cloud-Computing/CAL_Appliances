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

RQ_QUEUES = {
    'default': {
        'HOST': '172.17.0.3',
        'PORT': 6379,
        'DB': 0,
        'PASSWORD': 'secret',
        'DEFAULT_TIMEOUT': 360,
    }
}

MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'
