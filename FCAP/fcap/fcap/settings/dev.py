from base import *

# #########################################################

# ##### DEBUG CONFIGURATION ###############################
DEBUG = True


# ##### APPLICATION CONFIGURATION #########################

INSTALLED_APPS = DEFAULT_APPS

INSTALLED_APPS.extend([
    'authentication',
    'management',
])

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'fcap',
        'HOST': '172.17.0.2',
        'USER': 'root',
        'PASSWORD': '',
        'PORT': 3306,
    }
}