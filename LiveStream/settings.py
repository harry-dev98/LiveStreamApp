import os
import re

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SECRET_KEY = 'ds-7twz6fb(n4llog&ktj1fu6kstps+957(%hp%#843582@zp6'

DEBUG = True

ALLOWED_HOSTS = ['*']


# Application definition
INSTALLED_APPS = [
    'channels',
    'LiveStreamApp',
    'rest_framework',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'LiveStream.urls'


TEMPLATE_DIR = os.path.join(BASE_DIR,'templates')
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [TEMPLATE_DIR],
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

WSGI_APPLICATION = 'LiveStream.wsgi.application'
ASGI_APPLICATION = 'LiveStream.asgi.application'

CHANNEL_REDIS_HOST = [('127.0.0.1',6379)]
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": CHANNEL_REDIS_HOST,
            "symmetric_encryption_keys": [SECRET_KEY],
            "capacity":1000000,
            "channel_capacity": {
                "http.request": 2000000,
                "http.response!*": 100000,
                re.compile(r"^websocket.send\!.+"): 200000,
            },
        },
        # 'ROUTING': 'LiveStreamApp.routing.route_patterns',

    },
}


# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}


# Password validation
# https://docs.djangoproject.com/en/3.0/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/3.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

# TIME_ZONE = 'UTC'
TIME_ZONE =  'Asia/Kolkata'

USE_I18N = True

USE_L10N = True

USE_TZ = False


STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')
