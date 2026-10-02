#!/bin/sh
# Name: Word Wise Diagnostic
# Author: Kindle Word Wise Skill
# Read-only internal checks. Exported logs/settings are private; do not publish them.
set -eu
out=/mnt/us/WordWiseDiagnostics
mkdir -p "$out"
printf 'started\n' > "$out/status.txt"
pref=/var/local/java/prefs/language_layer.preferences
if test -r "$pref"; then
 cp -p "$pref" "$out/language_layer.preferences"
else
 printf 'Language-layer preference file not found.\n' > "$out/preference-error.txt"
fi
test ! -r /mnt/us/system/version.txt || cp /mnt/us/system/version.txt "$out/version.txt"
ls -la /mnt/us/system/kll > "$out/dictionary-files.txt" 2>&1 || :
if command -v showlog >/dev/null 2>&1; then
 showlog 2>/dev/null | grep -iE 'KLL_|word.?wise|language.?layer|GlossController|GlossModel|SQLite.*(error|fail)' | tail -n 600 > "$out/native-log.txt" || :
fi
if command -v sqlite3 >/dev/null 2>&1; then
 : > "$out/sidecar-checks.txt"
 for file in /mnt/us/documents/*.sdr/LanguageLayer.en.*.kll; do
  test -f "$file" || continue
  printf '\n%s\n' "$file" >> "$out/sidecar-checks.txt"
  sqlite3 -readonly "$file" 'SELECT key,value FROM metadata; SELECT COUNT(*) FROM glosses; PRAGMA integrity_check;' >> "$out/sidecar-checks.txt" 2>&1 || :
 done
fi
printf 'complete\n' > "$out/status.txt"
sync
printf 'Word Wise diagnostic complete. Reconnect USB for inspection.\n'
