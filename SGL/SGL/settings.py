"""
Django settings for SGL project.

Generated by 'django-admin startproject' using Django 5.2.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.2/ref/settings/
"""
import os
from pathlib import Path
from celery.schedules import crontab
from django.urls import reverse_lazy

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-b(-jf@^9b8=m19+6m000yz=klwz4(%4ktil=m25n9(q14te-85'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    'users',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core',
    'patients',
    'patient_portal',
    'samples',
    'results',
    'reports',
    'analysis',
    'channels',
    'integrations',
    'equipment',
    'analytics',
    'tests',
    'simple_history',
    'billing',


    'crispy_forms',
    'crispy_bootstrap5',
    'django_tables2',
    'django_filters',
    'widget_tweaks',
    'import_export',
    'rest_framework',
    'auditlog',
    'django_pandas',


]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'auditlog.middleware.AuditlogMiddleware',
    'patient_portal.middleware.PortalAccessMiddleware',

]

ROOT_URLCONF = 'SGL.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates']
        ,
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

WSGI_APPLICATION = 'SGL.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']  # For development
STATIC_ROOT = BASE_DIR / 'staticfiles'


# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
AUTH_USER_MODEL = 'users.User'
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_REDIRECT_URL = 'login'
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"
ADMIN_SITE_HEADER = "LabManager Administration"
ADMIN_SITE_TITLE = "LabManager Admin Portal"
ADMIN_INDEX_TITLE = "Admin page"

SESSION_COOKIE_AGE = 1209600  # 2 weeks in seconds
SESSION_SAVE_EVERY_REQUEST = True
SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
SESSION_COOKIE_HTTPONLY = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = False


# settings.py
EMAIL_HOST = 'localhost'  # Your local machine
EMAIL_PORT = 2525
EMAIL_HOST_USER = ''
EMAIL_HOST_PASSWORD = '4E889F9E3597BA781C5F28D4AEEA5848125D'
DEFAULT_FROM_EMAIL = 'thirdthe3rd1ne.com'

CELERY_BEAT_SCHEDULE = {
    'cleanup_old_records': {
        'task': 'core.tasks.cleanup_old_records',
        'schedule': crontab(day_of_week=1, hour=0),  # Every Monday at midnight
    },
}

PLOTLY_COMPONENTS = [
    'dash_core_components',
    'dash_html_components',
    'dash_renderer',
    'dpd_components'
]

HL7_TIMESTAMP_FORMAT = '%Y%m%d%H%M%S'  # HL7 format: 20240207123045

# FHIR/HL7 Configuration
HL7_OID = "1.2.3.4.5"  # Your organization's OID
FHIR_SERVER_URL = "https://hapi.fhir.org/baseR4"  # Test server
ASGI_APPLICATION = 'SGL.asgi.application'
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [("127.0.0.1", 6379)],
        },
    },
}
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',          # Main app
]


ACCOUNT_USER_MODEL_USERNAME_FIELD = 'username'
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = True
ACCOUNT_AUTHENTICATION_METHOD = 'username_email'


FHIR_SERVER_URL = "https://hapi.fhir.org/baseR4"  # Public test server

# base directory
LOGS_DIR = os.path.join(BASE_DIR, 'logs')




# Logging config
LOGS_DIR = BASE_DIR / 'logs'
LOGS_DIR.mkdir(exist_ok=True)  # Create directory if it doesn't exist

#  log file paths and related -ish
DEBUG_LOG_PATH = str(LOGS_DIR / 'debug.log')
ANALYSIS_LOG_PATH = str(LOGS_DIR / 'analysis.log')

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'debug_file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': DEBUG_LOG_PATH,
            'formatter': 'verbose'
        },
        'analysis_file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': ANALYSIS_LOG_PATH,
            'formatter': 'verbose'
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'debug_file'],
            'level': 'INFO',
            'propagate': True,
        },
        'analysis': {
            'handlers': ['console', 'analysis_file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}
LOGS_DIR = os.path.join(BASE_DIR, 'logs')
DEBUG_LOG = os.path.join(LOGS_DIR, 'debug.log')
ANALYSIS_LOG = os.path.join(LOGS_DIR, 'analysis.log')

# task auto report to doc
CELERY_BEAT_SCHEDULE = {
    'send-daily-reports': {
        'task': 'reports.tasks.send_daily_reports',
        'schedule': crontab(hour=8, minute=0),  # 8 AM daily
    },
}

from dotenv import load_dotenv
import os

load_dotenv()  # Load .env file

JULIUS_API_KEY = os.getenv('JULIUS_API_KEY')
MOCK_RESULTS = os.getenv('MOCK_MODE', 'False').lower() == 'true'

# Clinic Information
SITE_NAME = "LiS0 Labos"
SITE_ADDRESS = "ave.Mokhtar Ould Daddah, Tevragh Zeina, Nouakchott"
SITE_PHONE = "+22243786398"
SITE_EMAIL = "Lis0Labs@Lab.clinic.com"
SITE_BILLING_PHONE = "(555) 5555555"

# Ensure these settings exist
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
SITE_URL = 'http://localhost:8000'  # Change to your actual domain

LAB_NAME = "LiS0"