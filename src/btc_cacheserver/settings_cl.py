"""
Django settings for btc_cacheserver project.

Generated by 'django-admin startproject' using Django 2.0.

For more information on this file, see
https://docs.djangoproject.com/en/2.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.0/ref/settings/
"""

import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'v$v15$r(&he1m+tl8-ogj%t&osbg8hv)0$^%%-nq=-b+x$3oco'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ["*"]


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'btc_cacheserver.contract',
    'channels',
    'corsheaders'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'btc_cacheserver.urls'

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

WSGI_APPLICATION = 'btc_cacheserver.wsgi.application'


# Database
# https://docs.djangoproject.com/en/2.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE'  : 'django.db.backends.mysql',
        'NAME'    : 'blockchain',
        'USER'    : 'root',
        'PASSWORD': 'h7wFdCZN2NubZonbXAs1mYUf',
        'HOST'    : '10.2.0.5',
        'PORT'    : 3306,
    }
}

# Password validation
# https://docs.djangoproject.com/en/2.0/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/2.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

CORS_ORIGIN_ALLOW_ALL = False
CORS_ALLOW_CREDENTIALS = True
CORS_ORIGIN_WHITELIST = ("localhost:4200")
# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.0/howto/static-files/

STATIC_URL = '/static/'

LOGGING = {
'version': 1,
'disable_existing_loggers': False,
'formatters': {
'django':{
'format': '[%(asctime)s] [%(threadName)s:%(thread)d] [%(name)s] [%(pathname)s:%(lineno)s] [%(funcName)s] [%(levelname)s]-%(message)s', 'datefmt': '%Y-%m-%d %H:%M:%S'}
},
'filters': {
},
'handlers': {
'mail_admins': {
'level': 'ERROR',
'class': 'django.utils.log.AdminEmailHandler',
'include_html': True,
},
'console':{
'level': 'DEBUG',
'class': 'logging.StreamHandler',
'formatter': 'django'
},
'request_handler': {
'level':'DEBUG',
'class':'logging.handlers.TimedRotatingFileHandler',
'filename': './data/logs/app_bsmserver.log',
'backupCount': 5,
'formatter':'django',
},
'scprits_handler': {
'level':'DEBUG',
'class':'logging.handlers.TimedRotatingFileHandler',
'filename':'./data/logs/app_bsmserver.log',
'backupCount': 5,
'formatter':'django',
}
},
'loggers': {
'django': {
'handlers': ['request_handler', 'console'],
'level': 'ERROR',
'propagate': False
},
'django.request': {
'handlers': ['request_handler'],
'level': 'ERROR',
'propagate': False,
},
'scripts': {
'handlers': ['scprits_handler'],
'level': 'INFO',
'propagate': False
},
'django.db.backends': {
'handlers': ['request_handler'],
'level': 'ERROR',
'propagate': False
}
}
}

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "asgiref.inmemory.ChannelLayer",
        "ROUTING": "btc_cacheserver.blockchain.routing.channel_routing",
    },
}

CONTRACT_DIR = os.path.join(BASE_DIR, "sol")
INTERFACE_ABI_FILE = BASE_DIR + "/sol/Interface-abi.json"
INTERFACE_SOL_FILE = BASE_DIR + "/sol/Interface.sol"
USER_CONTRACT_ABI_FILE = "./test-user-contract-abi.json"
USERLOAN_FILE = BASE_DIR + '/sol/UserLoan.json'

BLOCKCHAIN_ACCOUNT        = "0x3b2BD2ad09FC693119736b6E038Cd2343B9F8D2a"
BLOCKCHAIN_PASSWORD       = "123456"
BLOCKCHAIN_CALL_GAS_LIMIT = 4500000
TRANSACTION_MAX_WAIT      = 600


