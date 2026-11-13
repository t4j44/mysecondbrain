import io
import asyncio
import os
import subprocess
import sys
import tarfile
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

from cryptography.exceptions import InvalidTag

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'restore'))
from encrypt_backup import decrypt, encrypt, read_bounded, transform
from pilot_restore import comparison, restore_list
from staging_recovery import archive_bytes, close_and_remove_dump, private_directory, run_private_dump, staging_url, unpack_private

PHRASE = 'Synthetic recovery phrase for tests only'


class PrivateRecoveryTests(unittest.TestCase):
    def test_cancelled_dump_waits_for_thread_and_removes_plaintext(self):
        with tempfile.TemporaryDirectory() as root:
            dump = Path(root) / 'synthetic.dump'
            release = threading.Event()
            async def scenario():
                started = asyncio.Event()
                loop = asyncio.get_running_loop()
                def fake_dump(**options):
                    loop.call_soon_threadsafe(started.set)
                    if not release.wait(5):
                        raise RuntimeError('Synthetic worker not released')
                    dump.write_bytes(b'synthetic')
                    return dump
                with patch('staging_recovery.run_backup', side_effect=fake_dump):
                    task = asyncio.create_task(run_private_dump())
                    await started.wait()
                    task.cancel()
                    await asyncio.sleep(0)
                    self.assertFalse(task.done())
                    release.set()
                    with self.assertRaises(asyncio.CancelledError):
                        await task
                    self.assertFalse(dump.exists())
            try:
                asyncio.run(scenario())
            finally:
                release.set()

    def test_oversize_encrypted_file_rejected_before_open(self):
        with tempfile.TemporaryDirectory() as root:
            source = Path(root) / 'synthetic.enc'
            source.write_bytes(b'12345')
            with patch.object(Path, 'open') as opened:
                with self.assertRaises(ValueError):
                    read_bounded(source, maximum=4)
                opened.assert_not_called()

    def test_file_growth_cannot_escape_read_limit(self):
        with tempfile.TemporaryDirectory() as root:
            source = Path(root) / 'synthetic.enc'
            source.write_bytes(b'1')
            with patch.object(Path, 'open', return_value=io.BytesIO(b'12345')):
                with self.assertRaises(ValueError):
                    read_bounded(source, maximum=4)

    @unittest.skipUnless(os.name == 'nt', 'Windows DACL regression')
    def test_private_directory_rejects_existing_explicit_other_user_access(self):
        with tempfile.TemporaryDirectory() as root:
            private = Path(root) / 'private'
            self.assertEqual(private_directory(private), private)
            sentinel = private / 'synthetic.txt'
            sentinel.write_text('synthetic only', encoding='utf-8')
            self.assertEqual(private_directory(private), private)
            subprocess.run(['icacls', str(private), '/grant', '*S-1-1-0:(OI)(CI)R'],
                check=True, capture_output=True)
            try:
                with self.assertRaises(subprocess.CalledProcessError):
                    private_directory(private)
                self.assertEqual(sentinel.read_text(encoding='utf-8'), 'synthetic only')
            finally:
                subprocess.run(['icacls', str(private), '/remove:g', '*S-1-1-0'],
                    check=True, capture_output=True)

    def test_oversize_dump_rejected_before_opening_content(self):
        with tempfile.TemporaryDirectory() as root:
            dump = Path(root) / 'input.dump'
            dump.write_bytes(b'12345')
            with patch('staging_recovery.MAX_DUMP_BYTES', 4), patch.object(Path, 'open') as opened:
                with self.assertRaises(ValueError):
                    archive_bytes(dump, {})
                opened.assert_not_called()

    def test_oversize_manifest_rejected_before_opening_dump(self):
        with tempfile.TemporaryDirectory() as root:
            dump = Path(root) / 'input.dump'
            dump.write_bytes(b'synthetic')
            with patch('staging_recovery.MAX_MANIFEST_BYTES', 8), patch.object(Path, 'open') as opened:
                with self.assertRaises(ValueError):
                    archive_bytes(dump, {'tables': ['synthetic']})
                opened.assert_not_called()

    def test_oversize_member_does_not_create_partial_plaintext(self):
        stream = io.BytesIO()
        with tarfile.open(fileobj=stream, mode='w:gz') as archive:
            for name, value in [('database.dump', b'12345'), ('manifest.json', b'{}')]:
                member = tarfile.TarInfo(name)
                member.size = len(value)
                archive.addfile(member, io.BytesIO(value))
        with tempfile.TemporaryDirectory() as root, patch('staging_recovery.MAX_DUMP_BYTES', 4):
            with self.assertRaises(ValueError):
                unpack_private(stream.getvalue(), root)
            self.assertEqual(list(Path(root).iterdir()), [])

    def test_plaintext_removed_when_connection_close_fails(self):
        with tempfile.TemporaryDirectory() as root:
            dump = Path(root) / 'synthetic.dump'
            dump.write_bytes(b'synthetic')
            conn = AsyncMock()
            conn.close.side_effect = RuntimeError('synthetic close failure')
            with self.assertRaises(RuntimeError):
                asyncio.run(close_and_remove_dump(conn, dump))
            self.assertFalse(dump.exists())

    def test_cleanup_failure_is_not_reported_as_success(self):
        with patch.object(Path, 'unlink', side_effect=PermissionError('synthetic')):
            with self.assertRaises(PermissionError):
                asyncio.run(close_and_remove_dump(AsyncMock(), Path('synthetic.dump')))

    def test_restore_selection_keeps_schema_grants_and_excludes_managed_objects(self):
        entries = [
            '9; 2615 1 SCHEMA - auth postgres',
            '10; 0 0 ACL - SCHEMA auth postgres',
            '11; 0 0 DEFAULT ACL - DEFAULT PRIVILEGES FOR TABLES postgres',
            '12; 0 1 TABLE DATA public memories postgres',
            '13; 0 1 ACL public TABLE memories postgres',
            '14; 0 1 FUNCTION auth uid() postgres',
            '15; 0 1 TABLE DATA vault secrets supabase_admin',
            '16; 3079 1 EXTENSION - vector',
        ]
        self.assertEqual(restore_list('\n'.join(entries)).splitlines(), entries[1:6])
        with self.assertRaises(ValueError):
            restore_list(entries[-1])

    def test_authenticated_roundtrip_and_fresh_nonce(self):
        payload = b'Only synthetic fixture bytes'
        first, second = encrypt(payload, PHRASE), encrypt(payload, PHRASE)
        self.assertNotEqual(first, second)
        self.assertEqual(decrypt(first, PHRASE), payload)

    def test_wrong_phrase_and_tampering_fail(self):
        original = encrypt(b'Synthetic fixture', PHRASE)
        with self.assertRaises(InvalidTag):
            decrypt(original, PHRASE + 'wrong')
        for position in (5, 21, 34, len(original) - 1):
            altered = bytearray(original)
            altered[position] ^= 1
            with self.assertRaises(InvalidTag):
                decrypt(bytes(altered), PHRASE)

    def test_bad_envelope_and_short_phrase_fail(self):
        for value in (b'', b'SBBK1', b'unknown' * 10):
            with self.assertRaises(ValueError):
                decrypt(value, PHRASE)
        with self.assertRaises(ValueError):
            encrypt(b'a', 'short')

    def test_unauthenticated_plaintext_is_never_written(self):
        with tempfile.TemporaryDirectory() as root:
            source, target = Path(root) / 'source', Path(root) / 'plain'
            source.write_bytes(encrypt(b'Synthetic fixture', PHRASE))
            with self.assertRaises(InvalidTag):
                transform('dec', source, target, PHRASE + 'wrong')
            self.assertFalse(target.exists())

    def test_existing_destination_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as root:
            source, target = Path(root) / 'source', Path(root) / 'existing'
            source.write_bytes(b'synthetic')
            target.write_bytes(b'preserved')
            with self.assertRaises(FileExistsError):
                transform('enc', source, target, PHRASE)
            self.assertEqual(target.read_bytes(), b'preserved')

    def test_staging_only_connection_guard(self):
        allowed = 'postgresql://postgres.rpkjmdrralzxhdsgceal:synthetic@aws-0-test.pooler.supabase.com:5432/postgres'
        self.assertEqual(staging_url(allowed), allowed)
        for bad in (allowed.replace('rpkjmdrralzxhdsgceal', 'production'),
                allowed.replace(':5432/', ':6543/'), allowed.replace('/postgres', '/other'),
                allowed + '?host=production.example.invalid', allowed + '?user=other',
                allowed.replace('pooler.supabase.com', 'pooler.supabase.com.attacker.test'),
                'postgresql://postgres:synthetic@127.0.0.1:5432/postgres'):
            with self.assertRaises(ValueError):
                staging_url(bad)

    def test_archive_roundtrip_has_only_dump_and_private_manifest(self):
        with tempfile.TemporaryDirectory() as root:
            folder = Path(root)
            dump = folder / 'input.dump'
            dump.write_bytes(b'Synthetic PostgreSQL custom dump')
            out = folder / 'restore'
            out.mkdir()
            unpack_private(decrypt(encrypt(archive_bytes(dump, {'tables': []}), PHRASE), PHRASE), out)
            self.assertEqual((out / 'database.dump').read_bytes(), dump.read_bytes())
            self.assertEqual(sorted(p.name for p in out.iterdir()), ['database.dump', 'manifest.json'])

    def test_traversal_extra_members_and_links_rejected(self):
        for member_name, kind in (('../escape', tarfile.REGTYPE), ('database.dump', tarfile.SYMTYPE)):
            stream = io.BytesIO()
            with tarfile.open(fileobj=stream, mode='w:gz') as archive:
                entry = tarfile.TarInfo(member_name)
                entry.type, entry.linkname = kind, 'elsewhere'
                archive.addfile(entry)
                archive.addfile(tarfile.TarInfo('manifest.json'))
            with tempfile.TemporaryDirectory() as root, self.assertRaises(ValueError):
                unpack_private(stream.getvalue(), root)

    def test_comparison_detects_record_and_security_drift(self):
        sections = ('tables', 'columns', 'policies', 'functions', 'constraints', 'indexes', 'triggers', 'schemas', 'default_acl')
        original = {name: [{'digest': 'synthetic', 'acl': '{a,b}'}] for name in sections}
        equivalent = {name: [{'digest': 'synthetic', 'acl': '{b,a}'}] for name in sections}
        self.assertTrue(all(comparison(original, equivalent).values()))
        for section in sections:
            changed = {**equivalent, section: [{'digest': 'changed', 'acl': '{b,a}'}]}
            self.assertFalse(comparison(original, changed)[section])

    def test_comparison_checks_roles_memberships_and_extension_versions(self):
        source = {name: [] for name in ('tables', 'columns', 'policies', 'functions',
            'constraints', 'indexes', 'triggers', 'schemas', 'default_acl')}
        source.update(roles=[{'rolname': 'synthetic', 'rolcanlogin': True, 'rolsuper': False}],
            memberships=[{'role': 'anon', 'member': 'synthetic', 'inherit_option': False}],
            extensions=[{'extname': 'vector', 'extversion': '0.8.2', 'owner': 'synthetic'}])
        restored = {**source, 'roles': [{'rolname': 'synthetic', 'rolcanlogin': False, 'rolsuper': False}]}
        self.assertTrue(all(comparison(source, restored).values()))
        self.assertFalse(comparison(source, {**restored, 'roles': source['roles']})['source_role_logins_disabled'])
        self.assertFalse(comparison(source, {**restored, 'memberships': []})['role_memberships'])
        self.assertFalse(comparison(source, {**restored, 'extensions': []})['extension_versions'])


if __name__ == '__main__':
    unittest.main()
