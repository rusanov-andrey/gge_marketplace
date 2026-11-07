from .base import *


DEBUG = True

SECRET_KEY = '123'
MEDIA_ROOT = ''


SQLITE_DB_DIR = ''


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

CELERY_BROKER_URL = ''
