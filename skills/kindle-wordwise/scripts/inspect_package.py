#!/usr/bin/env python3
"""Read-only standalone AZW3/Word Wise inspector. Python 3.10+, stdlib only."""
import argparse
import hashlib
import json
import re
import sqlite3
import struct
from pathlib import Path


def require(condition, message):
    if not condition:
        raise ValueError(message)


def book_identity(path):
    data = Path(path).read_bytes()
    require(len(data) >= 86, 'Truncated Palm database')
    count = struct.unpack_from('>H', data, 76)[0]
    require(count > 0 and 78 + count * 8 <= len(data), 'Invalid Palm record directory')
    offsets = [struct.unpack_from('>I', data, 78 + n * 8)[0] for n in range(count)]
    require(offsets == sorted(set(offsets)) and offsets[-1] < len(data), 'Invalid Palm offsets')
    first = data[offsets[0]:offsets[1] if count > 1 else len(data)]
    require(len(first) >= 132 and first[16:20] == b'MOBI', 'Missing MOBI header')
    require(struct.unpack_from('>H', first, 12)[0] == 0, 'Encrypted books are unsupported')
    require(struct.unpack_from('>I', first, 36)[0] == 8, 'Expected standalone KF8/AZW3')
    require(not any(data[a:(offsets[n+1] if n+1 < count else len(data))] == b'BOUNDARY'
                    for n, a in enumerate(offsets)), 'Combined MOBI is unsupported')
    codec_id = struct.unpack_from('>I', first, 28)[0]
    require(codec_id in (65001, 1252), 'Unsupported MOBI character encoding')
    codec = 'utf-8' if codec_id == 65001 else 'cp1252'
    header_size = struct.unpack_from('>I', first, 20)[0]
    exth = 16 + header_size
    require(first[exth:exth+4] == b'EXTH', 'Missing EXTH metadata')
    size, records = struct.unpack_from('>II', first, exth+4)
    require(exth+size <= len(first) and size >= 12, 'Invalid EXTH size')
    values = {}
    pos = exth + 12
    for _ in range(records):
        require(pos+8 <= exth+size, 'Truncated EXTH entry')
        key, length = struct.unpack_from('>II', first, pos)
        require(length >= 8 and pos+length <= exth+size, 'Invalid EXTH entry size')
        value = first[pos+8:pos+length]
        require(key not in values or key not in (113, 501, 504), 'Duplicate identity metadata')
        values[key] = value
        pos += length
    asin = (values.get(113) or values.get(504) or b'').decode(codec)
    require(re.fullmatch(r'B[0-9A-Z]{9}', asin), 'Missing or invalid Kindle ASIN')
    if values.get(113) and values.get(504):
        require(values[113] == values[504], 'ASIN metadata fields disagree')
    cde = values.get(501, b'').decode(codec)
    require(cde == 'EBOK', 'Expected EBOK content type')
    locale = struct.unpack_from('>I', first, 92)[0]
    require(locale & 0xff == 9, 'Book locale must be English')
    return {'asin': asin, 'acr': data[:32].rstrip(b'\0').decode('utf-8'),
            'revision': first[32:36].hex(), 'content_type': cde,
            'sha256': hashlib.sha256(data).hexdigest()}


def connect_readonly(path):
    return sqlite3.connect(Path(path).resolve().as_uri() + '?mode=ro', uri=True)


def inspect(book, layer=None, dictionary=None, raw_html=None):
    book = Path(book)
    identity = book_identity(book)
    expected = f"LanguageLayer.en.{identity['asin']}.kll"
    if layer is None:
        matches = list(book.with_suffix('.sdr').glob(expected))
        require(len(matches) == 1, 'Exactly one matching .sdr sidecar is required')
        layer = matches[0]
    layer = Path(layer)
    require(layer.name == expected, 'Sidecar filename/ASIN mismatch')
    with connect_readonly(layer) as db:
        require(db.execute('PRAGMA integrity_check').fetchone()[0] == 'ok', 'Sidecar integrity failed')
        pairs = db.execute('SELECT key, value FROM metadata').fetchall()
        require(len({k for k, _ in pairs}) == len(pairs), 'Duplicate sidecar metadata keys')
        meta = dict(pairs)
        require(meta.get('acr') == identity['acr'], 'Sidecar ACR mismatch')
        require(meta.get('bookRevision') == identity['revision'], 'Sidecar revision mismatch')
        require(meta.get('sourceLanguage') == 'en', 'Expected English sidecar source')
        rows = db.execute('SELECT start, end, difficulty, sense_id FROM glosses ORDER BY start').fetchall()
        require(rows, 'No annotations were generated')
        for start, end, difficulty, sense in rows:
            require(isinstance(start, int) and start >= 0, 'Invalid start offset')
            require(end is None or isinstance(end, int) and end > start, 'Invalid end offset')
            require(isinstance(difficulty, int) and 0 <= difficulty <= 5, 'Invalid difficulty')
            require(isinstance(sense, int), 'Invalid sense ID')
    result = {'book': str(book), 'sidecar': str(layer), **identity, 'gloss_count': len(rows),
              'sidecar_integrity': 'ok', 'identity_match': True,
              'offsets_checked': False, 'dictionary_checked': False, 'screen_verified': False}
    if raw_html is not None:
        raw = Path(raw_html).read_bytes()
        for start, end, _, _ in rows:
            require(start < len(raw) and (end is None or end <= len(raw)), 'Annotation outside KF8 bytes')
            require(raw[start] not in b'<> \t\r\n' and not 128 <= raw[start] < 192,
                    'Annotation starts at markup, whitespace or UTF-8 continuation')
        result['offsets_checked'] = True
    if dictionary is not None:
        with connect_readonly(dictionary) as db:
            require(db.execute('PRAGMA integrity_check').fetchone()[0] == 'ok', 'Dictionary integrity failed')
            columns = {r[1] for r in db.execute('PRAGMA table_info(senses)')}
            id_column = next((n for n in ('id', 'sense_id') if n in columns), None)
            require(id_column, 'Unrecognized senses schema')
            available = {r[0] for r in db.execute(f'SELECT {id_column} FROM senses')}
            missing = {sense for _, _, _, sense in rows} - available
            require(not missing, f'{len(missing)} sense IDs missing from selected dictionary')
            if 'metadata' in {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}:
                result['dictionary_metadata'] = dict(db.execute('SELECT key, value FROM metadata'))
        result['dictionary_checked'] = True
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--book', type=Path, required=True)
    parser.add_argument('--layer', type=Path)
    parser.add_argument('--dictionary', type=Path)
    parser.add_argument('--raw-html', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    try:
        result = inspect(args.book, args.layer, args.dictionary, args.raw_html)
    except (ValueError, OSError, sqlite3.Error, UnicodeError, struct.error) as error:
        parser.exit(1, f'Inspection failed: {error}\n')
    rendered = json.dumps(result, ensure_ascii=False, indent=2) + '\n'
    if args.output:
        args.output.write_text(rendered, encoding='utf-8')
    print(rendered, end='')


if __name__ == '__main__':
    main()
