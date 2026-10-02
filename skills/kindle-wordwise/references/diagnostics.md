# Enabled, but no hints

Do not infer a slider exists from an enabled menu switch. In the confirmed failure the bottom-right area showed only reading percentage.

1. Identify the open title/author, firmware, USB path and ASIN. Distinguish a cloud copy from the matched USB book without assuming user error.
2. Verify sidecar name, ACR/revision, SQLite integrity and annotations against the final book. Fix a missing/mismatched package before changing device settings.
3. Check actual gloss language and native dictionary integrity/sense coverage. Ordinary lookup dictionaries are separate.
4. Inspect actual language-layer preferences and native logs. Include `KLL_`, WordWise, LanguageLayer, GlossController, GlossModel and SQLite failures: narrower filters can omit decisive evidence. USB-mount-time disk I/O errors do not alone prove corruption.

## Existing SH Integration

`device_probe.sh` requires an already working launcher. It creates `/mnt/us/WordWiseDiagnostics`, exports `/var/local/java/prefs/language_layer.preferences`, firmware/dictionary listings, read-only metadata and integrity queries for sidecars, and relevant logs. It does not export firmware libraries/catalog, change settings, restart, install a jailbreak or alter dictionaries. Keep preferences and logs private.

Stage as `documents/Word Wise Diagnostic.sh`, safely eject and ask the user to launch **Word Wise Diagnostic**. Reconnect after its completion message. Check `status.txt=complete` and copy exports to a private case directory. If output does not appear, investigate the launcher; do not repeatedly request blind launch/reconnect cycles.

Without working authorized internal access, restrict actions to UI and USB-visible files. The preference is not ordinarily accessible through USB. Do not quietly add a jailbreak or claim an internal fix ran.

## Conditional first-use repair

Read [confirmed-case.md](confirmed-case.md). Preconditions: absent native body hints despite enabled UI; valid matching book/annotations and dictionary; actual flat settings have `isEnabled=true`, the intended `targetLang`, and absent or exactly false `ftuxShown`; the repair and existing internal access are authorized.

```sh
python3 scripts/build_first_use_repair.py --preferences /private/case/language_layer.preferences --gloss-language zh --output /private/case/fix
```

The generator rejects unfamiliar Java-properties syntax, duplicate/namespaced keys, continuations, disabled/mismatched settings and an already-true flag. The generated script checks the entire live snapshot before writing. If settings changed since export, re-export and regenerate; do not bypass the guard.

Read the manifest and generated scripts. Stage **both** scripts in `documents`, but no private exported settings. **Word Wise First Use Fix** saves before/after copies under `/mnt/us/WordWiseFirstUseRepair`, atomically adds only `ftuxShown=true` while preserving mode/ownership, records status and prints manual-restart instructions. It does not change dictionary, language, enabled state, difficulty, catalog or reading files, and never automatically reboots.

Ask the user to restart from the Kindle menu and check body text. Retrieve status/backups at the next useful connection. Generated/copied is not executed; executed is not screen-confirmed. If hints remain absent, inspect new evidence rather than adding guessed flags.

**Word Wise First Use Undo** is for requested rollback only. It refuses to overwrite settings if they have changed since repair; otherwise it restores the exact backup atomically and asks for manual restart. Do not undo a working setup just to test it.

Keep private backups until success is confirmed. Once copied locally, remove only this task's scripts and exports when connected; leave shared launcher software and unrelated files intact.
