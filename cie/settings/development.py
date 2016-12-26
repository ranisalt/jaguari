from .base import *

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.10/howto/deployment/checklist/

ALLOWED_HOSTS = ['localhost']

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'knmo&y7or4!sxfqab74_-923od*rih36f5!2=f_#x!t%pjkdoc'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# Database
# https://docs.djangoproject.com/en/1.10/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': path.join(BASE_DIR, 'db.sqlite3'),
    },
}

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.10/howto/static-files/
STATIC_ROOT = path.join(BASE_DIR, 'static')

# File upload configuration
MEDIA_ROOT = path.join(BASE_DIR, 'media')

# Student database credentials
CAGR_KEY = ('', '')

# Payment gateway configuration
PAGSEGURO_EMAIL = 'dce@contato.ufsc.br'
PAGSEGURO_TOKEN = ''
PAGSEGURO_SANDBOX = True
PAGSEGURO_LOG_IN_MODEL = True
