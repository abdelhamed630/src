from email.utils import formataddr
from pathlib import Path
import os
import environ
from datetime import timedelta

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env()
environ.Env.read_env(BASE_DIR / '.env')

SECRET_KEY    = os.getenv('SECRET_KEY')
DEBUG         = os.getenv('DEBUG', 'False') == 'True'
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost').split(',')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Third-party
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'django_filters',
    # Local
    'accounts',
    'products',
    'cart',
    'orders',
    'chat',
    'reviews',
    'wishlist',
    'notifications',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'corsheaders.middleware.CorsMiddleware',
]

ROOT_URLCONF      = 'E_Commerce.urls'
WSGI_APPLICATION  = 'E_Commerce.wsgi.application'

TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [BASE_DIR / 'templates'],
    'APP_DIRS': True,
    'OPTIONS': {'context_processors': [
        'django.template.context_processors.request',
        'django.contrib.auth.context_processors.auth',
        'django.contrib.messages.context_processors.messages',
    ]},
}]

# ── Database ──────────────────────────────────────────────────────────
DATABASES = {
    'default': {
        'ENGINE'      : os.getenv('DATABASE_ENGINE', 'django.db.backends.postgresql'),
        'NAME'        : os.getenv('DATABASE_NAME', 'E_Commerce'),
        'USER'        : os.getenv('DATABASE_USER', 'postgres'),
        'PASSWORD'    : os.getenv('DATABASE_PASSWORD', ''),
        'HOST'        : os.getenv('DATABASE_HOST', 'db'),
        'PORT'        : os.getenv('DATABASE_PORT', '5432'),
        'OPTIONS'     : {'connect_timeout': 10},
        'CONN_MAX_AGE': 60,
    }
}

AUTH_USER_MODEL = 'accounts.User'

# ── Cache — Django built-in Redis (no django-redis needed) ────────────
REDIS_URL = os.getenv('REDIS_URL', 'redis://redis:6379/0')

CACHES = {
    'default': {
        'BACKEND' : 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': REDIS_URL,
        'TIMEOUT' : 300,
    }
}

# Use DB for sessions (stable, no Redis dependency for auth)
SESSION_ENGINE = 'django.contrib.sessions.backends.db'

# ── DRF ───────────────────────────────────────────────────────────────
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '30/minute',
        'user': '120/minute',
    },
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
}

# ── JWT ───────────────────────────────────────────────────────────────
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME'   : timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME'  : timedelta(days=7),
    'ROTATE_REFRESH_TOKENS'   : True,
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_HEADER_TYPES'       : ('Bearer',),
}

# ── CORS ──────────────────────────────────────────────────────────────
CORS_ALLOWED_ORIGINS   = os.getenv('CORS_ALLOWED_ORIGINS', 'http://localhost:3000').split(',')
CORS_ALLOW_CREDENTIALS = True

# ── Celery ────────────────────────────────────────────────────────────
CELERY_BROKER_URL        = REDIS_URL
CELERY_RESULT_BACKEND    = REDIS_URL
CELERY_ACCEPT_CONTENT    = ['json']
CELERY_TASK_SERIALIZER   = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE          = 'Africa/Cairo'
CELERY_BEAT_SCHEDULE = {
    'cleanup-expired-otps': {
        'task'    : 'accounts.tasks.cleanup_expired_otps',
        'schedule': 3600,
    },
    'expire-old-carts': {
        'task'    : 'cart.tasks.expire_old_carts',
        'schedule': 86400,
    },
}

# ── Email ─────────────────────────────────────────────────────────────
EMAIL_BACKEND       = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST          = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT          = int(os.getenv('EMAIL_PORT', 587))
EMAIL_USE_TLS       = True
EMAIL_HOST_USER     = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL  = formataddr(("ShopZone", EMAIL_HOST_USER))

GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')

# ── Media & Static ────────────────────────────────────────────────────
MEDIA_URL  = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
STATIC_URL    = '/static/'
STATIC_ROOT   = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# ── Security ──────────────────────────────────────────────────────────
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS             = 'DENY'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE      = 'en-us'
TIME_ZONE          = 'Africa/Cairo'
USE_I18N           = True
USE_TZ             = True
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

CORS_ALLOW_ALL_ORIGINS = True  # للـ development
