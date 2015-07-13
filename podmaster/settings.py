"""
Django settings for podmaster project.

Generated by 'django-admin startproject' using Django 1.8.2.

For more information on this file, see
https://docs.djangoproject.com/en/1.8/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.8/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.8/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET', 'p)r2w-c!m^znb%2ppj0rxp9uu$+$q928w#*$41y5(eu$friqqv')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', 'True') == 'True'

if DEBUG:
    ALLOWED_HOSTS = ['*']
else:
    ALLOWED_HOSTS = ['host.podmaster.io']


# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'podcasts',
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

ROOT_URLCONF = 'podmaster.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.jinja2.Jinja2',
        'APP_DIRS': True,
        'DIRS': [
            os.path.join(BASE_DIR, 'templates', 'jinja2'),
        ],
        'OPTIONS': {
            'environment': 'podmaster.jinja2_helper.environment',
        },
    },
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'podmaster.wsgi.application'

ADMINS = [
    ('basta', 'mattbasta@gmail.com'),
]

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
        },
    },
}


# Database
# https://docs.djangoproject.com/en/1.8/ref/settings/#databases

DATABASES = {}
try:
    import dj_database_url
    prod_db = dj_database_url.config()
    assert prod_db, 'No DB config found...'
    print 'Using prod database'
    DATABASES['default'] = prod_db
    DATABASES['default']['ENGINE'] = 'django_postgrespool'
except Exception:
    print 'Using SQLite db'
    DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }


# Internationalization
# https://docs.djangoproject.com/en/1.8/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = False


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.8/howto/static-files/

STATIC_URL = '/static/'
STATICFILES_DIRS = STATIC_DIRS = (
    os.path.join(BASE_DIR, 'static'),
)
STATIC_ROOT = STATIC_DIRS[0] + 'root'

STATICFILES_STORAGE = 'whitenoise.django.GzipManifestStaticFilesStorage'


GETCONNECT_IO_PID = os.environ.get('GETCONNECT_IO_PID')
GETCONNECT_IO_QUERY_KEY = os.environ.get('GETCONNECT_IO_QUERY_KEY')
GETCONNECT_IO_PUSH_KEY = os.environ.get('GETCONNECT_IO_PUSH_KEY')

S3_BUCKET = os.environ.get('S3_BUCKET')
S3_ACCESS_ID = os.environ.get('S3_ACCESS_ID')
S3_SECRET_KEY = os.environ.get('S3_SECRET_KEY')

LAMBDA_ACCESS_SECRET = os.environ.get('LAMBDA_ACCESS_SECRET')

DEPLOY_SLACKBOT_URL = os.environ.get('DEPLOY_SLACKBOT_URL')

EMAIL_USE_TLS = True
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_HOST_USER = os.environ.get('GMAIL_USER')
EMAIL_HOST_PASSWORD = os.environ.get('GMAIL_PASS')
EMAIL_PORT = 587

MAX_FILE_SIZE = 1024 * 1024 * 256

try:
    from settings_local import *
except ImportError:
    pass
