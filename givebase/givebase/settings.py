import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-4_y5-6^!9ark)#&0q=kjq7$i=nn0m5w96dd%v$)&wgy1cm36^m'

# PRODUCTION: Turn off debug
DEBUG = True

# Allow only your domains in production
ALLOWED_HOSTS = [
    "umanity.xyz",
    "www.umanity.xyz",
    "miniapp.umanity.xyz",
    "127.0.0.1",  # Optional for local testing
    "localhost"
]

# CSRF: Trusted Origins for HTTPS
CSRF_TRUSTED_ORIGINS = [
    "https://umanity.xyz",
    "https://www.umanity.xyz",
    "https://miniapp.umanity.xyz",
]

# Use secure cookies in production
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'core',
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
    'core.middleware.COOPMiddleware',  # ADD THIS LINE

]

ROOT_URLCONF = 'givebase.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / 'core' / 'templates',  # Point to core app templates
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'givebase.wsgi.application'

# SQLite for now — consider PostgreSQL for production
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Point to your core app's static directory
STATICFILES_DIRS = [
    BASE_DIR / 'core' / 'templates' / 'static',  # Your actual static files location
]

# Static files finders
STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
]

# CORS for production
CORS_ALLOWED_ORIGINS = [
    "https://umanity.xyz",
    "https://www.umanity.xyz",
    "https://miniapp.umanity.xyz",
    "https://keys.coinbase.com",  # ADD THIS
    "http://localhost:8000",      # For local testing
    "http://127.0.0.1:8000",
    "http://localhost:3000",  # Next.js dev server

]

CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_CREDENTIALS = True

# X-Frame-Options - Allow Base Account
X_FRAME_OPTIONS = 'ALLOWALL'  # Or 'SAMEORIGIN'

# IMPORTANT: Set COOP policy
SECURE_CROSS_ORIGIN_OPENER_POLICY = None  # Critical for Base Account SDK!

CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'