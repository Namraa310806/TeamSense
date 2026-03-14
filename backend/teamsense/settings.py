import os
import logging
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'django-insecure-teamsense-dev-key-change-in-production')

DEBUG = os.getenv('DEBUG', 'True').lower() in ('true', '1', 'yes')

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '*').split(',')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Third-party
    'rest_framework',
    'corsheaders',
    'django_celery_results',
    # Local apps
    'core',
    'employees',
    'meetings',
    'analytics',
    'ai_engine',
    'ingestion',
    'accounts',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'teamsense.urls'

TEMPLATES = [
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

WSGI_APPLICATION = 'teamsense.wsgi.application'

# Database - SQLite for development, PostgreSQL for production
# Local SQLite (no Docker)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

CELERY_BROKER_URL = 'redis://localhost:6379/0'  # Local Redis
CELERY_RESULT_BACKEND = 'django-db'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 50,
}

# CORS
CORS_ALLOW_ALL_ORIGINS = True

# Celery
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = 'django-db'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'
CELERY_TASK_ALWAYS_EAGER = os.getenv('CELERY_TASK_ALWAYS_EAGER', 'False').lower() in ('true', '1', 'yes')
CELERY_TASK_EAGER_PROPAGATES = True

# OpenAI
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '').strip()
OPENAI_KEY_STRICT = os.getenv('OPENAI_KEY_STRICT', 'False').lower() in ('true', '1', 'yes')


def _mask_secret(value: str) -> str:
    if not value:
        return 'missing'
    if len(value) <= 10:
        return '***masked***'
    return f"{value[:7]}...{value[-4:]}"


_settings_logger = logging.getLogger(__name__)
if not OPENAI_API_KEY:
    msg = 'OPENAI_API_KEY not found in environment variables.'
    if OPENAI_KEY_STRICT:
        raise RuntimeError(msg)
    _settings_logger.warning('%s OpenAI-backed features will use fallback behavior.', msg)
else:
    _settings_logger.info('OpenAI API key loaded (masked=%s)', _mask_secret(OPENAI_API_KEY))

# Embedding dimensions
EMBEDDING_DIMENSIONS = 1536

# Upload limits for meeting recording ingestion
DATA_UPLOAD_MAX_MEMORY_SIZE = 209715200  # 200 MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 52428800   # 50 MB in-memory, rest streamed to disk

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s %(levelname)s %(name)s %(message)s',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
        },
    },
    'loggers': {
        '': {
            'handlers': ['console'],
            'level': os.getenv('LOG_LEVEL', 'INFO'),
        },
        'django': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
            'propagate': False,
        },
        'ai_engine': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'ai_services': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'meetings': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
