from .base import *

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')
MEDIA_ROOT = os.environ['FILE_STORAGE_BASE_PATH']


SQLITE_DB_DIR = os.environ['SQLITE_DB_DIR']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': Path(SQLITE_DB_DIR) / 'db.sqlite3',
    }
}

CELERY_BROKER_URL = os.environ['CELERY_BROKER_URL']
