import os
import sqlite3
import tempfile

from django.test import SimpleTestCase

from local_server import EXPECTED_CAFINO_TABLES, restore_sqlite_backup, sqlite_backup, verify_sqlite_backup


def build_cafino_like_database(path, marker=None):
    connection=sqlite3.connect(path)
    try:
        for table in sorted(EXPECTED_CAFINO_TABLES):
            if table=='django_migrations':
                connection.execute('CREATE TABLE django_migrations (id INTEGER PRIMARY KEY, app TEXT, name TEXT)')
                connection.execute("INSERT INTO django_migrations(app,name) VALUES('core','0001')")
            else:
                connection.execute(f'CREATE TABLE {table} (id INTEGER PRIMARY KEY)')
        if marker is not None:
            connection.execute('CREATE TABLE backup_marker (value TEXT)')
            connection.execute('INSERT INTO backup_marker(value) VALUES(?)',(marker,))
        connection.commit()
    finally:
        connection.close()


class LocalBackupVerificationTests(SimpleTestCase):
    def test_valid_cafino_backup_has_integrity_schema_and_checksum(self):
        with tempfile.TemporaryDirectory() as root:
            source=os.path.join(root,'cafino.sqlite3')
            build_cafino_like_database(source)
            result=verify_sqlite_backup(source)
            self.assertTrue(result['ok'])
            self.assertEqual(result['integrity'],'ok')
            self.assertEqual(result['foreign_key_violations'],0)
            self.assertEqual(result['missing_tables'],[])
            self.assertEqual(len(result['sha256']),64)
            self.assertGreater(result['migration_rows'],0)

    def test_non_cafino_or_corrupt_file_is_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            empty_db=os.path.join(root,'empty.sqlite3')
            sqlite3.connect(empty_db).close()
            missing=verify_sqlite_backup(empty_db)
            self.assertFalse(missing['ok'])
            self.assertIn('django_migrations',missing['missing_tables'])

            corrupt=os.path.join(root,'corrupt.sqlite3')
            with open(corrupt,'wb') as handle:handle.write(b'not-a-sqlite-database')
            result=verify_sqlite_backup(corrupt)
            self.assertFalse(result['ok'])
            self.assertIn('error',result)

    def test_backup_and_restore_are_verified_and_copy_data(self):
        with tempfile.TemporaryDirectory() as root:
            source=os.path.join(root,'source.sqlite3')
            backup_path=os.path.join(root,'backup.sqlite3')
            target=os.path.join(root,'target.sqlite3')
            build_cafino_like_database(source,marker='source-marker')
            build_cafino_like_database(target,marker='old-target')

            backup_result=sqlite_backup(source,backup_path)
            self.assertTrue(backup_result['ok'])
            restore_result=restore_sqlite_backup(backup_path,target)
            self.assertTrue(restore_result['ok'])
            self.assertEqual(restore_result['stage'],'restored')

            connection=sqlite3.connect(target)
            try:
                marker=connection.execute('SELECT value FROM backup_marker').fetchone()[0]
            finally:
                connection.close()
            self.assertEqual(marker,'source-marker')
