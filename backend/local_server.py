import os,sys,sqlite3
os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.settings')

def db_path():
    from django.conf import settings
    return str(settings.DATABASES['default']['NAME'])

def sqlite_backup(source,target):
    src=sqlite3.connect(source);dst=sqlite3.connect(target);src.backup(dst);dst.close();src.close()

if __name__=='__main__':
    import django
    django.setup()
    from django.core.management import call_command
    if '--process-notifications' in sys.argv:
        call_command('process_notifications');raise SystemExit(0)
    if '--backup' in sys.argv:
        target=sys.argv[sys.argv.index('--backup')+1];sqlite_backup(db_path(),target);raise SystemExit(0)
    if '--restore' in sys.argv:
        source=sys.argv[sys.argv.index('--restore')+1];sqlite_backup(source,db_path());raise SystemExit(0)
    call_command('migrate',interactive=False)
    call_command('collectstatic',interactive=False,verbosity=0)
    from django.core.wsgi import get_wsgi_application
    from wsgiref.simple_server import make_server
    application=get_wsgi_application()
    server=make_server('127.0.0.1',8000,application)
    server.serve_forever()
