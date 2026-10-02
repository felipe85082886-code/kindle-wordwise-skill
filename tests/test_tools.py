import hashlib
import importlib.util
import shutil
import sqlite3
import struct
import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / 'skills/kindle-wordwise/scripts'


def load(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


inspector = load('inspect_package')
builder = load('build_first_use_repair')
ASIN = 'B123456789'


def fixture(root):
    # Synthetic Palm/KF8 metadata only; no copyrighted ebook fixture.
    first = bytearray(280)
    first[16:20] = b'MOBI'
    struct.pack_into('>I', first, 20, 264)
    struct.pack_into('>I', first, 28, 65001)
    struct.pack_into('>I', first, 32, 0x12345678)
    struct.pack_into('>I', first, 36, 8)
    struct.pack_into('>I', first, 92, 9)
    entries = [(113, ASIN.encode()), (504, ASIN.encode()), (501, b'EBOK')]
    encoded = b''.join(struct.pack('>II', key, len(value)+8)+value for key, value in entries)
    first += b'EXTH' + struct.pack('>II', len(encoded)+12, len(entries)) + encoded
    header = bytearray(88)
    header[:13] = b'SyntheticBook'
    struct.pack_into('>H', header, 76, 1)
    struct.pack_into('>I', header, 78, len(header))
    book = root / 'Synthetic.azw3'
    book.write_bytes(header+first)
    layer = book.with_suffix('.sdr') / f'LanguageLayer.en.{ASIN}.kll'
    layer.parent.mkdir()
    with sqlite3.connect(layer) as c:
        c.execute('CREATE TABLE metadata(key TEXT,value TEXT)')
        c.executemany('INSERT INTO metadata VALUES(?,?)', [('acr', 'SyntheticBook'),
            ('bookRevision', '12345678'), ('sourceLanguage', 'en')])
        c.execute('CREATE TABLE glosses(start INTEGER PRIMARY KEY,end INTEGER,difficulty INTEGER,sense_id INTEGER)')
        c.execute('INSERT INTO glosses VALUES(3,8,2,101)')
    raw = root / 'raw.bin'
    raw.write_bytes(b'<p>Hello reader</p>')
    dictionary = root / 'dictionary.sqlite'
    with sqlite3.connect(dictionary) as c:
        c.execute('CREATE TABLE senses(id INTEGER PRIMARY KEY)')
        c.execute('INSERT INTO senses VALUES(101)')
    return book, layer, dictionary, raw


class PackageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.book, self.layer, self.dictionary, self.raw = fixture(self.root)

    def tearDown(self):
        self.temp.cleanup()

    def test_valid_package_readonly(self):
        before = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in (self.book,self.layer,self.dictionary)}
        result = inspector.inspect(self.book, dictionary=self.dictionary, raw_html=self.raw)
        self.assertTrue(result['identity_match'] and result['offsets_checked'] and result['dictionary_checked'])
        self.assertEqual(before, {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in before})

    def test_revision_mismatch(self):
        with sqlite3.connect(self.layer) as c:
            c.execute("UPDATE metadata SET value='bad' WHERE key='bookRevision'")
        with self.assertRaisesRegex(ValueError, 'revision mismatch'):
            inspector.inspect(self.book)

    def test_missing_sense(self):
        with sqlite3.connect(self.dictionary) as c:
            c.execute('DELETE FROM senses')
        with self.assertRaisesRegex(ValueError, 'sense IDs missing'):
            inspector.inspect(self.book, dictionary=self.dictionary)

    def test_bad_offsets(self):
        with sqlite3.connect(self.layer) as c:
            c.execute('UPDATE glosses SET start=0,end=1')
        with self.assertRaisesRegex(ValueError, 'markup'):
            inspector.inspect(self.book, raw_html=self.raw)

    def test_missing_sidecar(self):
        self.layer.unlink()
        with self.assertRaisesRegex(ValueError, 'sidecar'):
            inspector.inspect(self.book)

    def test_encrypted_book(self):
        data=bytearray(self.book.read_bytes());struct.pack_into('>H',data,88+12,1);self.book.write_bytes(data)
        with self.assertRaisesRegex(ValueError, 'Encrypted'):
            inspector.inspect(self.book)


class PreferenceTests(unittest.TestCase):
    prefs = b'#Synthetic settings\nisEnabled=true\ntargetLang=zh\ndifficulty=3\n'

    def test_single_change_and_no_reboot(self):
        repair, undo, manifest = builder.build(self.prefs, 'zh')
        expected = self.prefs + b'ftuxShown=true\n'
        self.assertEqual(manifest['after_sha256'], hashlib.sha256(expected).hexdigest())
        self.assertNotIn('/sbin/reboot', repair)
        self.assertNotIn('stop framework', repair)
        self.assertIn('Manually restart', repair)

    def test_reject_disabled_wrong_language_or_already_complete(self):
        for data in (self.prefs.replace(b'isEnabled=true',b'isEnabled=false'),
                     self.prefs.replace(b'targetLang=zh',b'targetLang=en'),
                     self.prefs+b'ftuxShown=true\n'):
            with self.subTest(data=data), self.assertRaises(ValueError):
                builder.build(data,'zh')

    def test_reject_duplicate_and_escaped_syntax(self):
        for data in (self.prefs+b'isEnabled=true\n', self.prefs+b'profile\\:enabled=true\n',
                     self.prefs.replace(b'\n',b'\r\n')):
            with self.subTest(data=data), self.assertRaises(ValueError):
                builder.build(data,'zh')

    def test_explicit_false(self):
        data=self.prefs+b'ftuxShown=false\n'
        _,_,manifest=builder.build(data,'zh')
        self.assertEqual(manifest['after_sha256'],hashlib.sha256(data.replace(b'ftuxShown=false',b'ftuxShown=true')).hexdigest())

    @unittest.skipUnless(shutil.which('sh'), 'POSIX shell required for private sandbox integration test')
    def test_repair_and_undo_and_stale_guards(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);pref=root/'preferences';pref.write_bytes(self.prefs);pref.chmod(0o640)
            dictionary=root/'dictionary';dictionary.write_bytes(b'synthetic')
            repair,undo,manifest=builder.build(self.prefs,'zh')
            def sandbox(source):
                return (source.replace('pref=/var/local/java/prefs/language_layer.preferences',f'pref={pref}')
                    .replace('/mnt/us/WordWiseFirstUseRepair/',str(root/'backup')+'/')
                    .replace('/mnt/us/system/kll/kll.en.zh.klld',str(dictionary)))
            fix=root/'fix.sh';fix.write_text(sandbox(repair));back=root/'undo.sh';back.write_text(sandbox(undo))
            # Stale export must stop without touching settings or creating a backup.
            pref.write_bytes(self.prefs+b'other=true\n')
            self.assertNotEqual(subprocess.run(['sh',str(fix)],capture_output=True).returncode,0)
            self.assertEqual(pref.read_bytes(),self.prefs+b'other=true\n')
            self.assertFalse((root/'backup').exists())
            pref.write_bytes(self.prefs)
            success=subprocess.run(['sh',str(fix)],capture_output=True,text=True)
            self.assertEqual(success.returncode,0,success.stderr+success.stdout)
            self.assertEqual(pref.read_bytes(),self.prefs+b'ftuxShown=true\n')
            self.assertEqual(pref.stat().st_mode & 0o777,0o640)
            # Subsequent user settings must be preserved rather than rolled back.
            pref.write_bytes(pref.read_bytes()+b'other=true\n')
            self.assertNotEqual(subprocess.run(['sh',str(back)],capture_output=True).returncode,0)
            self.assertTrue(pref.read_bytes().endswith(b'other=true\n'))
            pref.write_bytes(self.prefs+b'ftuxShown=true\n')
            restored=subprocess.run(['sh',str(back)],capture_output=True,text=True)
            self.assertEqual(restored.returncode,0,restored.stderr+restored.stdout)
            self.assertEqual(pref.read_bytes(),self.prefs)


if __name__ == '__main__':
    unittest.main()
