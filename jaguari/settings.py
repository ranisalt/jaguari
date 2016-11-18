"""
Django settings for jaguari project.

Generated by 'django-admin startproject' using Django 1.8.

For more information on this file, see
https://docs.djangoproject.com/en/1.8/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.8/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
import string
from six.moves.urllib.parse import urljoin

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.8/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '=z!p8$bbgw+9g$xc5qvo2=s$)1-_0lga2pe-=)1uuvhm@dr_45'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []

# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_cas_ng',
    'accounts',
    'requests',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
)

AUTHENTICATION_BACKENDS = (
    # 'django.contrib.auth.backends.ModelBackend',
    'django_cas_ng.backends.CASBackend',
)

USE_CODE_ALPHABET = string.ascii_uppercase + string.digits

USE_CODE_LENGTH = 10

CAS_EXTRA_LOGIN_PARAMS = {
    'userType': 'padrao',
    'convertToUserType': 'alunoGraduacao',
    'lockUserType': '1',
}

CAGR_CREDENTIALS = ('', '',)

CAGR_WEBSERVICE_URL = 'https://ws.ufsc.br/'

CAGR_DEGREE_URL = urljoin(CAGR_WEBSERVICE_URL,
                                  'CAGRService/cursoGraduacaoAluno/')

CAGR_INFO_URL = urljoin(CAGR_WEBSERVICE_URL,
                                'CadastroPessoaService/vinculosPessoaById/')

CAS_LOGOUT_COMPLETELY = True

# CAS_REDIRECT_URL = 'https://cie.dce.ufsc.br/login'

CAS_SERVER_URL = 'https://cie.dce.ufsc.br/'

CAS_USERNAME_ATTRIBUTE = 'idPessoa'

CAS_VERSION = 'CAS_2_SAML_1_0'

ROOT_URLCONF = 'jaguari.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'jaguari.wsgi.application'

# Database
# https://docs.djangoproject.com/en/1.8/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

# Internationalization
# https://docs.djangoproject.com/en/1.8/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.8/howto/static-files/

STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]

STATIC_URL = '/static/'

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
