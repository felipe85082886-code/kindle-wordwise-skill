#!/usr/bin/env python3
"""Generate a private, snapshot-guarded first-use repair and exact-backup undo."""
import argparse
import hashlib
import json
import re
from pathlib import Path


def parse_preferences(raw):
    if b'\x00' in raw:
        raise ValueError('Binary preference format is unsupported')
    text = raw.decode('utf-8')
    if not text.endswith('\n') or '\r' in text or '\\' in text:
        raise ValueError('Expected LF-terminated plain properties without escapes/continuations')
    values = {}
    for line in text.splitlines():
        if not line or line.startswith(('#', '!')):
            continue
        key, separator, value = line.partition('=')
        if not separator or not re.fullmatch(r'[A-Za-z][A-Za-z0-9_.-]*', key):
            raise ValueError('Unfamiliar or namespaced property syntax; no repair generated')
        if key in values:
            raise ValueError(f'Duplicate preference key: {key}')
        values[key] = value
    return text, values


def build(raw, language):
    text, values = parse_preferences(raw)
    if language not in ('zh', 'en'):
        raise ValueError('Only native zh/en gloss language is supported by this generator')
    if values.get('isEnabled') != 'true' or values.get('targetLang') != language:
        raise ValueError('Enabled state or gloss language does not match the diagnosis')
    if values.get('ftuxShown') == 'true':
        raise ValueError('First-use state is already complete; investigate another cause')
    if 'ftuxShown' in values and values['ftuxShown'] != 'false':
        raise ValueError('Unexpected first-use value')
    if 'ftuxShown' in values:
        after = text.replace('\nftuxShown=false\n', '\nftuxShown=true\n')
        if text.startswith('ftuxShown=false\n'):
            after = 'ftuxShown=true\n' + text[len('ftuxShown=false\n'):]
    else:
        after = text + 'ftuxShown=true\n'
    before_hash = hashlib.sha256(raw).hexdigest()
    after_bytes = after.encode('utf-8')
    after_hash = hashlib.sha256(after_bytes).hexdigest()
    common = '''set -eu
pref=/var/local/java/prefs/language_layer.preferences
out=/mnt/us/WordWiseFirstUseRepair/CASE_ID
fail() { printf 'Stopped: %s\\n' "$1"; exit 1; }
digest() {
 if command -v sha256sum >/dev/null 2>&1; then sha256sum "$1" | awk '{print $1}'
 elif command -v shasum >/dev/null 2>&1; then shasum -a 256 "$1" | awk '{print $1}'
 elif command -v busybox >/dev/null 2>&1; then busybox sha256sum "$1" | awk '{print $1}'
 else fail 'No SHA-256 utility; no settings changed.'; fi
}
test -r "$pref" || fail 'Expected preference file not found.'
'''.replace('CASE_ID', before_hash[:16])
    repair = '#!/bin/sh\n# Name: Word Wise First Use Fix\n# Author: Kindle Word Wise Skill\n' + common + f'''
test "$(digest "$pref")" = '{before_hash}' || fail 'Live settings changed since export; regenerate from a fresh snapshot.'
test -s '/mnt/us/system/kll/kll.en.{language}.klld' || fail 'Selected native dictionary missing.'
mkdir -p "$out"
test ! -e "$out/before.preferences" || fail 'Existing backup; inspect prior repair before retrying.'
test ! -e "$pref.wordwise-first-use.tmp" || fail 'Incomplete repair temporary file exists.'
cp -p "$pref" "$out/before.preferences"
'''
    if 'ftuxShown' in values:
        repair += '''sed 's/^ftuxShown=false$/ftuxShown=true/' "$pref" > "$out/new.preferences"\n'''
    else:
        repair += '''cat "$pref" > "$out/new.preferences"
printf 'ftuxShown=true\\n' >> "$out/new.preferences"
'''
    repair += f'''
test "$(digest "$out/new.preferences")" = '{after_hash}' || fail 'New settings verification failed; original preserved.'
test "$(digest "$pref")" = '{before_hash}' || fail 'Live settings changed during preparation; original preserved.'
cp -p "$pref" "$pref.wordwise-first-use.tmp"
cat "$out/new.preferences" > "$pref.wordwise-first-use.tmp"
mv "$pref.wordwise-first-use.tmp" "$pref"
cp -p "$pref" "$out/after.preferences"
printf 'patched-manual-restart-required\\n' > "$out/status.txt"
sync
printf 'First-use flag repaired. Manually restart Kindle from its menu, then check body text.\\n'
'''
    undo = '#!/bin/sh\n# Name: Word Wise First Use Undo\n# Author: Kindle Word Wise Skill\n' + common + f'''
test -r "$out/before.preferences" && test -r "$out/after.preferences" || fail 'Repair backups missing.'
test "$(digest "$out/before.preferences")" = '{before_hash}' || fail 'Original backup does not match this repair.'
test "$(digest "$out/after.preferences")" = '{after_hash}' || fail 'After-backup does not match this repair.'
test "$(digest "$pref")" = '{after_hash}' || fail 'Settings changed after repair; rollback would overwrite them.'
test ! -e "$pref.wordwise-first-use.tmp" || fail 'Temporary file already exists.'
cp -p "$out/before.preferences" "$pref.wordwise-first-use.tmp"
mv "$pref.wordwise-first-use.tmp" "$pref"
printf 'restored-manual-restart-required\\n' > "$out/status.txt"
sync
printf 'Original settings restored. Manually restart Kindle.\\n'
'''
    return repair, undo, {'before_sha256': before_hash, 'after_sha256': after_hash,
                         'change': {'ftuxShown': {'before': values.get('ftuxShown'), 'after': 'true'}},
                         'gloss_language': language, 'manual_restart_required': True,
                         'device_backup_directory': f'/mnt/us/WordWiseFirstUseRepair/{before_hash[:16]}',
                         'executed': False, 'screen_verified': False}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--preferences', type=Path, required=True)
    p.add_argument('--gloss-language', choices=('zh', 'en'), required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    try:
        repair, undo, manifest = build(a.preferences.read_bytes(), a.gloss_language)
        if a.output.exists() and any(a.output.iterdir()):
            raise ValueError('Output directory must be new or empty; preserve previous case files')
        a.output.mkdir(parents=True, exist_ok=True)
        for name, content in [('Word Wise First Use Fix.sh', repair), ('Word Wise First Use Undo.sh', undo)]:
            path = a.output / name
            path.write_text(content, encoding='utf-8')
            path.chmod(0o700)
        (a.output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    except (ValueError, OSError, UnicodeError) as error:
        p.exit(1, f'No repair generated: {error}\n')
    print('Generated snapshot-guarded repair and undo. Inspect before staging; restart manually after execution.')


if __name__ == '__main__':
    main()
