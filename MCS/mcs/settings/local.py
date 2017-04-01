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

MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'
