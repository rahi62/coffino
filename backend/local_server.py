import hashlib
import json
import os
import shutil
import sqlite3
import sys
import tempfile
from datetime import datetime, timezone

os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.settings')

EXPECTED_CAFINO_TABLES={
    'django_migrations',
    'businesses_business',
    'businesses_branch',
    'orders_order',
    'payments_payment',
}


def db_path():
    from django.conf import settings
    database=settings.DATABASES['default']
    engine=str(database.get('ENGINE') or '')
    if not engine.endswith('sqlite3'):
        raise RuntimeError('Local backup/restore only supports SQLite deployments')
    return str(database['NAME'])


def _sha256(path):
    digest=hashlib.sha256()
    with open(path,'rb') as handle:
        for chunk in iter(lambda:handle.read(1024*1024),b''):
            digest.update(chunk)
    return digest.hexdigest()


def verify_sqlite_backup(path,require_cafino=True):
    path=os.path.abspath(str(path))
    result={
        'ok':False,
        'path':path,
        'size_bytes':0,
        'sha256':'',
        'integrity':'unknown',
        'foreign_key_violations':0,
        'missing_tables':[],
        'migration_rows':0,
        'verified_at':datetime.now(timezone.utc).isoformat(),
    }
    if not os.path.isfile(path):
        result['error']='Backup file does not exist'
        return result
    try:
        result['size_bytes']=os.path.getsize(path)
        if result['size_bytes']<=0:
            result['error']='Backup file is empty'
            return result
        uri=f"file:{path.replace(os.sep,'/')}?mode=ro"
        connection=sqlite3.connect(uri,uri=True,timeout=10)
        try:
            integrity_rows=connection.execute('PRAGMA integrity_check').fetchall()
            integrity_ok=bool(integrity_rows) and all(str(row[0]).lower()=='ok' for row in integrity_rows)
            result['integrity']='ok' if integrity_ok else '; '.join(str(row[0]) for row in integrity_rows[:10])
            fk_rows=connection.execute('PRAGMA foreign_key_check').fetchall()
            result['foreign_key_violations']=len(fk_rows)
            tables={row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
            if require_cafino:
                result['missing_tables']=sorted(EXPECTED_CAFINO_TABLES-tables)
            if 'django_migrations' in tables:
                result['migration_rows']=int(connection.execute('SELECT COUNT(*) FROM django_migrations').fetchone()[0])
            result['table_count']=len(tables)
        finally:
            connection.close()
        result['sha256']=_sha256(path)
        result['ok']=(
            result['integrity']=='ok'
            and result['foreign_key_violations']==0
            and not result['missing_tables']
        )
        if not result['ok'] and 'error' not in result:
            result['error']='SQLite verification failed'
        return result
    except Exception as exc:
        result['error']=f'{exc.__class__.__name__}: {exc}'
        return result


def sqlite_backup(source,target):
    source=os.path.abspath(str(source));target=os.path.abspath(str(target))
    os.makedirs(os.path.dirname(target),exist_ok=True)
    src=sqlite3.connect(source,timeout=30)
    try:
        dst=sqlite3.connect(target,timeout=30)
        try:
            src.backup(dst)
            dst.commit()
        finally:
            dst.close()
    finally:
        src.close()
    return verify_sqlite_backup(target)


def restore_sqlite_backup(source,target):
    verification=verify_sqlite_backup(source)
    if not verification['ok']:
        return {'ok':False,'stage':'source-verification','verification':verification,'error':'Backup source verification failed'}
    restored=sqlite_backup(source,target)
    return {
        'ok':bool(restored.get('ok')),
        'stage':'restored' if restored.get('ok') else 'target-verification',
        'source':verification,
        'restored':restored,
        'error':None if restored.get('ok') else 'Restored database verification failed',
    }


def backup_restore_drill(source,workdir=None):
    source=os.path.abspath(str(source))
    source_check=verify_sqlite_backup(source)
    if not source_check['ok']:
        return {'ok':False,'stage':'source-verification','source':source_check,'error':'Operational database is not a valid Cafino SQLite database'}
    root=tempfile.mkdtemp(prefix='cafino-restore-drill-',dir=workdir or None)
    backup_path=os.path.join(root,'backup.sqlite3')
    restored_path=os.path.join(root,'restored.sqlite3')
    try:
        backup_check=sqlite_backup(source,backup_path)
        if not backup_check['ok']:
            return {'ok':False,'stage':'backup','source':source_check,'backup':backup_check,'error':'Temporary backup failed verification'}
        restore_result=restore_sqlite_backup(backup_path,restored_path)
        if not restore_result['ok']:
            return {'ok':False,'stage':'restore','source':source_check,'backup':backup_check,'restore':restore_result,'error':'Temporary restore failed verification'}
        restored_check=restore_result['restored']
        return {
            'ok':True,
            'stage':'complete',
            'source_sha256':source_check['sha256'],
            'backup_sha256':backup_check['sha256'],
            'restored_sha256':restored_check['sha256'],
            'source_size_bytes':source_check['size_bytes'],
            'backup_size_bytes':backup_check['size_bytes'],
            'restored_size_bytes':restored_check['size_bytes'],
            'verified_at':datetime.now(timezone.utc).isoformat(),
        }
    finally:
        shutil.rmtree(root,ignore_errors=True)


def _emit(payload,exit_code=None):
    print(json.dumps(payload,ensure_ascii=False))
    if exit_code is not None:
        raise SystemExit(exit_code)


if __name__=='__main__':
    import django
    django.setup()
    from django.core.management import call_command
    if '--process-notifications' in sys.argv:
        call_command('process_notifications');raise SystemExit(0)
    if '--verify-backup' in sys.argv:
        source=sys.argv[sys.argv.index('--verify-backup')+1]
        result=verify_sqlite_backup(source)
        _emit(result,0 if result['ok'] else 2)
    if '--backup' in sys.argv:
        target=sys.argv[sys.argv.index('--backup')+1]
        result=sqlite_backup(db_path(),target)
        _emit(result,0 if result['ok'] else 2)
    if '--restore' in sys.argv:
        source=sys.argv[sys.argv.index('--restore')+1]
        result=restore_sqlite_backup(source,db_path())
        _emit(result,0 if result['ok'] else 2)
    if '--drill-backup' in sys.argv:
        workdir=sys.argv[sys.argv.index('--drill-backup')+1] if sys.argv.index('--drill-backup')+1<len(sys.argv) else None
        result=backup_restore_drill(db_path(),workdir)
        _emit(result,0 if result['ok'] else 2)
    call_command('migrate',interactive=False)
    call_command('collectstatic',interactive=False,verbosity=0)
    from django.core.wsgi import get_wsgi_application
    from wsgiref.simple_server import make_server
    application=get_wsgi_application()
    server=make_server('127.0.0.1',8000,application)
    server.serve_forever()
