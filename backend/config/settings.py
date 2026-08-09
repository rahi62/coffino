import os
from pathlib import Path
from dotenv import load_dotenv
import dj_database_url

BASE_DIR=Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR/'.env')

SECRET_KEY=os.getenv('DJANGO_SECRET_KEY','dev-secret-change-me')
DEBUG=os.getenv('DJANGO_DEBUG','1')=='1'
ENVIRONMENT=os.getenv('CAF_INO_ENV','local')
ALLOWED_HOSTS=[x.strip() for x in os.getenv('DJANGO_ALLOWED_HOSTS','127.0.0.1,localhost').split(',') if x.strip()]

INSTALLED_APPS=[
 'django.contrib.admin','django.contrib.auth','django.contrib.contenttypes','django.contrib.sessions','django.contrib.messages','django.contrib.staticfiles',
 'corsheaders','rest_framework','django_filters','drf_spectacular',
 'apps.core','apps.businesses','apps.accounts','apps.catalog','apps.customers','apps.dining','apps.orders','apps.payments','apps.kitchen','apps.inventory',
 'apps.cashier','apps.takeaway','apps.dashboard','apps.suppliers','apps.purchasing','apps.accounting','apps.reports','apps.audit','apps.discounts','apps.workforce',
 'apps.production','apps.printing','apps.reservations','apps.loyalty','apps.notifications','apps.online_ordering','apps.delivery','apps.giftcards','apps.payment_gateway',
]
MIDDLEWARE=[
 'corsheaders.middleware.CorsMiddleware','django.middleware.security.SecurityMiddleware','whitenoise.middleware.WhiteNoiseMiddleware',
 'django.contrib.sessions.middleware.SessionMiddleware','django.middleware.common.CommonMiddleware','django.middleware.csrf.CsrfViewMiddleware',
 'django.contrib.auth.middleware.AuthenticationMiddleware','django.contrib.messages.middleware.MessageMiddleware',
]
ROOT_URLCONF='config.urls'
TEMPLATES=[{'BACKEND':'django.template.backends.django.DjangoTemplates','DIRS':[],'APP_DIRS':True,'OPTIONS':{'context_processors':['django.template.context_processors.request','django.contrib.auth.context_processors.auth','django.contrib.messages.context_processors.messages']}}]
WSGI_APPLICATION='config.wsgi.application';ASGI_APPLICATION='config.asgi.application'

default_db=f"sqlite:///{BASE_DIR/'db.sqlite3'}"
DATABASES={'default':dj_database_url.config(default=os.getenv('DATABASE_URL',default_db),conn_max_age=60,conn_health_checks=True)}

AUTH_USER_MODEL='accounts.User'
LANGUAGE_CODE='fa-ir';TIME_ZONE=os.getenv('DJANGO_TIME_ZONE','Asia/Tehran');USE_I18N=True;USE_TZ=True
STATIC_URL='/static/';STATIC_ROOT=BASE_DIR/'staticfiles'
STORAGES={'staticfiles':{'BACKEND':'whitenoise.storage.CompressedManifestStaticFilesStorage'}}
DEFAULT_AUTO_FIELD='django.db.models.BigAutoField'

CORS_ALLOWED_ORIGINS=[x.strip() for x in os.getenv('CORS_ALLOWED_ORIGINS','http://127.0.0.1:3000,http://localhost:3000').split(',') if x.strip()]
CSRF_TRUSTED_ORIGINS=[x.strip() for x in os.getenv('CSRF_TRUSTED_ORIGINS','').split(',') if x.strip()]
SECURE_PROXY_SSL_HEADER=('HTTP_X_FORWARDED_PROTO','https')
SESSION_COOKIE_SECURE=not DEBUG
CSRF_COOKIE_SECURE=not DEBUG
SECURE_CONTENT_TYPE_NOSNIFF=True
X_FRAME_OPTIONS='DENY'

REST_FRAMEWORK={
 'DEFAULT_PERMISSION_CLASSES':['rest_framework.permissions.IsAuthenticated'],
 'DEFAULT_AUTHENTICATION_CLASSES':['rest_framework_simplejwt.authentication.JWTAuthentication','rest_framework.authentication.SessionAuthentication'],
 'DEFAULT_FILTER_BACKENDS':['django_filters.rest_framework.DjangoFilterBackend','rest_framework.filters.SearchFilter'],
 'DEFAULT_SCHEMA_CLASS':'drf_spectacular.openapi.AutoSchema',
 'DEFAULT_THROTTLE_RATES':{'public_menu':'120/min','online_order':'20/min'},
}
SPECTACULAR_SETTINGS={'TITLE':'Cafino API','VERSION':'1.0.0'}

if not DEBUG:
    SECURE_SSL_REDIRECT=os.getenv('DJANGO_SECURE_SSL_REDIRECT','1')=='1'
    SECURE_HSTS_SECONDS=int(os.getenv('DJANGO_HSTS_SECONDS','3600'))
    SECURE_HSTS_INCLUDE_SUBDOMAINS=True
    SECURE_HSTS_PRELOAD=False
