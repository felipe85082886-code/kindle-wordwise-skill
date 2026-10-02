#!/usr/bin/env python3
"""Run under calibre-debug -e SCRIPT -- BOOK OUTPUT. No assertions needed."""
import sys
from pathlib import Path


def extract(book):
    from calibre.ebooks.mobi.reader.mobi6 import MobiReader
    from calibre.ebooks.mobi.reader.mobi8 import Mobi8Reader
    with Path(book).open('rb') as stream:
        reader = MobiReader(stream)
        if reader.kf8_type != 'standalone':
            raise ValueError('Expected a standalone KF8/AZW3 book')
        reader.check_for_drm()
        reader.extract_text()
        kf8 = Mobi8Reader(reader, reader.log)
        # Reconstruct in the part order used by WordDumb's KF8 byte offsets.
        kf8.kf8_sections = reader.sections
        kf8.read_indices()
        kf8.build_parts()
        return b''.join(kf8.parts)


if __name__ == '__main__':
    arguments = sys.argv[1:]
    if arguments and arguments[0] == '--':
        arguments.pop(0)
    if len(arguments) != 2:
        raise SystemExit('Usage: calibre-debug -e extract_kf8.py -- BOOK OUTPUT')
    Path(arguments[1]).write_bytes(extract(arguments[0]))
