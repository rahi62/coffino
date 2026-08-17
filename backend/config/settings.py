import os
from datetime import timedelta
from pathlib import Path

from corsheaders.defaults import default_headers
from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv
import dj_database_url

BASE_DIR=Path(__file__).resolve().parent.parent
env_file=Path(os.getenv('DJANGO_ENV_FILE',BASE_DIR/'.env'))
if not env_file.is_absolute():
    env_file=(BASE_DIR/env_file).resolve()
load_dotenv(env_file)

def _csv(name,default=''):
    return [x.strip() for x in os.getenv(name,default).split(',') if x.strip()]

def _append_unique(rows,*values):
    for value in values:
        value=str(value or '').strip()
        if value and value not in rows:
            rows.append(value)
    return rows

SECRET_KEY=os.getenv('DJANGO_SECRET_KEY','dev-secret-change-me')
DEBUG=os.getenv('DJANGO_DEBUG','1')=='1'
ENVIRONMENT=os.getenv('CAF_INO_ENV','local').strip().lower()
ALLOWED_HOSTS=_csv('DJANGO_ALLOWED_HOSTS','127.0.0.1,localhost')
railway_domain=os.getenv('RAILWAY_PUBLIC_DOMAIN','').strip()
if railway_domain:
    _append_unique(ALLOWED_HOSTS,railway_domain)

if not DEBUG and ENVIRONMENT in {'saas','dedicated'} and SECRET_KEY=='dev-secret-change-me':
    raise ImproperlyConfigured('DJANGO_SECRET_KEY must be configured for public Cafino deployments.')

CAF_INO_LICENSE_PUBLIC_KEY_PEM=os.getenv('CAF_INO_LICENSE_PUBLIC_KEY_PEM','')
CAF_INO_LICENSE_PUBLIC_KEY_PATH=os.getenv('CAF_INO_LICENSE_PUBLIC_KEY_PATH','')
CAF_INO_OPS_EVENT_RETENTION_DAYS=int(os.getenv('CAF_INO_OPS_EVENT_RETENTION_DAYS','90'))
CAF_INO_OPS_DIAGNOSTIC_RETENTION_DAYS=int(os.getenv('CAF_INO_OPS_DIAGNOSTIC_RETENTION_DAYS','30'))

INSTALLED_APPS=[
 'django.contrib.admin','django.contrib.auth','django.contrib.contenttypes','django.contrib.sessions','django.contrib.messages','django.contrib.staticfiles',
 'corsheaders','rest_framework','django_filters','drf_spectacular',
 'apps.core','apps.businesses','apps.accounts','apps.catalog','apps.customers','apps.dining','apps.orders','apps.payments','apps.kitchen','apps.inventory',
 'apps.cashier','apps.takeaway','apps.dashboard','apps.suppliers','apps.purchasing','apps.accounting','apps.reports','apps.audit','apps.discounts','apps.workforce',
 'apps.production','apps.printing','apps.reservations','apps.loyalty','apps.notifications','apps.online_ordering','apps.delivery','apps.giftcards','apps.payment_gateway','apps.operations',
]
MIDDLEWARE=[
 'corsheaders.middleware.CorsMiddleware','django.middleware.security.SecurityMiddleware','whitenoise.middleware.WhiteNoiseMiddleware',
 'django.contrib.sessions.middleware.SessionMiddleware','django.middleware.common.CommonMiddleware','django.middleware.csrf.CsrfViewMiddleware',
 'django.contrib.auth.middleware.AuthenticationMiddleware','django.contrib.messages.middleware.MessageMiddleware','django.middleware.clickjacking.XFrameOptionsMiddleware',
]
ROOT_URLCONF='config.urls'
TEMPLATES=[{'BACKEND':'django.template.backends.django.DjangoTemplates','DIRS':[],'APP_DIRS':True,'OPTIONS':{'context_processors':['django.template.context_processors.request','django.contrib.auth.context_processors.auth','django.contrib.messages.context_processors.messages']}}]
WSGI_APPLICATION='config.wsgi.application';ASGI_APPLICATION='config.asgi.application'

default_db=f"sqlite:///{BASE_DIR/'db.sqlite3'}"
DATABASES={'default':dj_database_url.config(
    default=os.getenv('DATABASE_URL',default_db),
    conn_max_age=int(os.getenv('DJANGO_DB_CONN_MAX_AGE','60')),
    conn_health_checks=True,
)}

AUTH_USER_MODEL='accounts.User'
LANGUAGE_CODE='fa'
LANGUAGES=(
 ('fa','فارسی'),
 ('en','English'),
)
TIME_ZONE=os.getenv('DJANGO_TIME_ZONE','Asia/Tehran');USE_I18N=True;USE_TZ=True
STATIC_URL='/static/';STATIC_ROOT=BASE_DIR/'staticfiles'
STORAGES={'staticfiles':{'BACKEND':'whitenoise.storage.CompressedManifestStaticFilesStorage'}}
DEFAULT_AUTO_FIELD='django.db.models.BigAutoField'

CORS_ALLOWED_ORIGINS=_csv('CORS_ALLOWED_ORIGINS','http://127.0.0.1:3000,http://localhost:3000')
CSRF_TRUSTED_ORIGINS=_csv('CSRF_TRUSTED_ORIGINS','')
frontend_origins=_csv('CAF_INO_FRONTEND_ORIGIN','')
for origin in frontend_origins:
    if not (origin.startswith('https://') or (DEBUG and origin.startswith('http://'))):
        raise ImproperlyConfigured('CAF_INO_FRONTEND_ORIGIN must use HTTPS outside DEBUG mode.')
    _append_unique(CORS_ALLOWED_ORIGINS,origin)
    _append_unique(CSRF_TRUSTED_ORIGINS,origin)

CORS_ALLOW_HEADERS=[*default_headers,'idempotency-key','x-cafino-override']
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
 'DEFAULT_THROTTLE_RATES':{'public_menu':'120/min','online_order':'20/min','ops_device':'60/min'},
}
SIMPLE_JWT={
 'ACCESS_TOKEN_LIFETIME':timedelta(days=1),
 'REFRESH_TOKEN_LIFETIME':timedelta(days=1),
}
CELERY_BROKER_URL=os.getenv('CELERY_BROKER_URL') or os.getenv('REDIS_URL') or 'redis://127.0.0.1:6379/0'
CELERY_TASK_SERIALIZER='json'
CELERY_ACCEPT_CONTENT=['json']
CELERY_RESULT_SERIALIZER='json'
CELERY_TASK_IGNORE_RESULT=True
CELERY_TIMEZONE=TIME_ZONE
CELERY_BEAT_SCHEDULE={
 'process-pending-notifications':{
  'task':'apps.notifications.tasks.process_pending_notifications',
  'schedule':60.0,
  'options':{'expires':55},
 },
 'prune-production-operations-history':{
  'task':'apps.operations.tasks.prune_operations_history',
  'schedule':86400.0,
  'options':{'expires':3600},
 },
}
SPECTACULAR_SETTINGS={'TITLE':'Cafino API','VERSION':'1.0.0'}

if not DEBUG:
    SECURE_SSL_REDIRECT=os.getenv('DJANGO_SECURE_SSL_REDIRECT','1')=='1'
    SECURE_HSTS_SECONDS=int(os.getenv('DJANGO_HSTS_SECONDS','3600'))
    SECURE_HSTS_INCLUDE_SUBDOMAINS=True
    SECURE_HSTS_PRELOAD=False
