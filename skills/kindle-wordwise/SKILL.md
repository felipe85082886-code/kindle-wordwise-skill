---
name: kindle-wordwise
description: Prepare English ebooks for native Kindle Word Wise with Chinese or English glosses, matching USB sidecars and library covers; diagnose enabled-but-missing hints, including the confirmed first-use failure on Paperwhite 5 firmware 5.19.2. Use for Kindle 生词提示 or 中文 Word Wise requests and operation of an authorized connected device. General translation and EPUB footnotes are separate workflows.
---

# Kindle Word Wise

Deliver native on-page glosses and a correct library cover. Carry out preparation, checks and USB transfer within the user's request. Ask for missing material facts or physical actions the agent cannot perform. A connected device does not authorize a jailbreak or firmware change.

## Each book

1. Prefer a DRM-free, reflowable English EPUB. Inspect title, author, language, navigation, images and cover. Hash and preserve the source; work on a copy. Route scanned PDFs to OCR first, and do not circumvent DRM.
2. Discover Calibre and WordDumb rather than assuming machine-specific paths. Read [production.md](references/production.md) for conversion, native Chinese dictionary selection, CLI operation and tool isolation. If `references/local-machine.md` exists, read it for this installation's private runtime locations; never publish that file. Use a durable tool location for repeated jobs; do not alter the user's proxy or existing Calibre configuration unnecessarily.
3. Finalize AZW3 text and metadata before generating its WordDumb sidecar. Keep final ASIN, EBOK type, Palm name/ACR, revision and `.sdr` name consistent. Text changes require regenerated annotations. Avoid soft-hyphen insertion.
4. Validate with `scripts/inspect_package.py`. For byte-offset verification, reconstruct the exact KF8 bytes with `scripts/extract_kf8.py` under Calibre and pass `--raw-html`. Pass the actual native dictionary with `--dictionary` to verify sense IDs. Report only checks performed; do not require an arbitrary minimum annotation count.
5. Create ASIN-keyed JPEG thumbnails with `scripts/make_cover.py` if Pillow is available. Follow the USB layout in [production.md](references/production.md). Back up exact existing files and reading records before an update. Merge intended files instead of replacing entire device directories; verify transferred hashes and eject safely.
6. Ask the user to open the exact title/author in English body text and check the library cover separately. A valid SQLite file alone is not device success.

## Enabled but no hints

Read [diagnostics.md](references/diagnostics.md). Check book identity/sidecar, actual language/dictionary and native errors before first-use state. Reading percentage is not a Word Wise control. Do not direct the user to a slider until a Word Wise entry is visible.

With an **already working** SH Integration launcher, `scripts/device_probe.sh` exports actual language-layer preferences, relevant logs and read-only database checks. Explain the read, stage the script, eject, have the user launch it and reconnect, then inspect status. Exports can contain private device data: keep them local. If the launcher fails, stop this route; do not quietly install or reactivate a jailbreak.

The first-use repair is conditional, not a per-book step. Confirmed on Paperwhite 5 firmware 5.19.2: valid annotations/dictionary, `isEnabled=true`, `targetLang=zh`, and absent `ftuxShown`. The new menu skipped the tutorial while the native handler still gated loading on first-use state. Adding **only** `ftuxShown=true` then **manually restarting** produced Chinese glosses. Automatic restart did not happen and must not be promised. Other firmware is not confirmed equivalent.

Once evidence justifies that repair, use `scripts/build_first_use_repair.py --preferences EXPORTED_PREF --gloss-language zh --output CASE_DIR`. It rejects disabled, mismatched, unfamiliar or already-complete settings and creates snapshot-guarded repair and rollback scripts. Within an authorized repair task, explain the one-setting change and backup, stage both scripts, have the user launch **Word Wise First Use Fix**, then manually restart from the Kindle menu. Do not apply this merely because hints are missing.

After screen verification, preserve private case records and remove only this task's launchers/exports when USB access is available. Preserve the book, reading progress, dictionary and working thumbnails; report pending cleanup when disconnected.

## Completion and public sharing

Report native gloss display and cover display separately. Distinguish prepared, transferred, executed and user-confirmed states. Keep source hashes, tool versions and repair status locally.

Publish only this skill, original helpers, synthetic tests and sanitized findings. Exclude books, proprietary dictionary databases, firmware/JAR exports, catalog databases, preferences, device logs and private paths. Evidence and upstream links: [confirmed-case.md](references/confirmed-case.md).
