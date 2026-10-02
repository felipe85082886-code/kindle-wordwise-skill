# Kindle Word Wise Codex Skill

[中文](README.md) · [Skill instructions](skills/kindle-wordwise/SKILL.md)

A reusable Codex skill for preparing English books with native Kindle Word Wise, Chinese glosses, matched USB sidecars and library thumbnails. Codex can perform the local conversion, verification, backup and transfer work; the reader supplies the book and confirms the device screen.

## Confirmed first-use failure

On a Paperwhite 5 (11th generation), firmware **5.19.2**, Word Wise was enabled and Chinese selected, but no body hints or bottom-right Word Wise entry appeared. The actual settings lacked `ftuxShown`. The new menu skipped the tutorial while native loading still depended on first-use state. Adding only `ftuxShown=true`, then **manually restarting**, restored Chinese glosses, confirmed by the user.

This is a conditional repair supported by one device/firmware case. It is not a required step for each book. Internal repair requires an already functioning authorized access method, such as SH Integration. This skill does not install a jailbreak. Automatic reboot did not work in the case and is not part of the reusable helper.

## Install

Ask Codex's skill-installer:

> Install skills/kindle-wordwise from https://github.com/felipe85082886-code/kindle-wordwise-skill.

Or copy `skills/kindle-wordwise` into your Codex skills directory, normally `~/.codex/skills/` or `%USERPROFILE%\.codex\skills\`. If `CODEX_HOME` is configured, use its `skills` directory. Back up an existing same-name skill before updating. Use it on a subsequent turn:

> Use $kindle-wordwise to prepare this English EPUB with native Chinese Word Wise and a correct cover, then verify and transfer it over USB.

## Workflow

1. Preserve the original DRM-free English EPUB and verify its metadata, text and images.
2. Use official Calibre and WordDumb to create the final AZW3 and matched native sense-ID sidecar.
3. Verify ASIN, ACR, revision, SQLite integrity, exact KF8 byte offsets and dictionary sense coverage.
4. Prepare ASIN-keyed thumbnails, back up existing book/reading files, merge intended files over USB and verify hashes.
5. Safely eject and confirm native body hints and the library cover separately.

No internal setting change is needed for the ordinary new-book workflow. Scanned PDFs need OCR first. Calibre's ordinary Send to device does not send WordDumb sidecars: use WordDumb's send function or the matched manual USB layout.

The skill includes read-only package inspection (standard Python 3.10+), Calibre KF8 extraction, an optional Pillow cover helper, a read-only device probe, and snapshot-guarded repair/undo generation. The repair changes one first-use property and refuses to overwrite newer settings. It keeps exact backups and requires manual restart.

See [production](skills/kindle-wordwise/references/production.md), [diagnostics](skills/kindle-wordwise/references/diagnostics.md) and [sanitized case evidence](skills/kindle-wordwise/references/confirmed-case.md). Dependencies: official [Calibre](https://calibre-ebook.com/download) and [WordDumb](https://github.com/xxyzz/WordDumb); neither is bundled here.

## Validation

The real package passed checks for 7,016 annotations, including exact offsets and native Chinese dictionary sense IDs. The user confirmed Chinese hints on screen. Visible library-cover recovery was not confirmed in that case. Compatibility with other firmware remains unconfirmed.

Run synthetic tests without books or a device:

```sh
python3 -m unittest discover -s tests -v
```

Tests cover valid/mismatched packages, missing senses, invalid offsets, encryption, ambiguous preferences, repair and exact rollback, and refusal to overwrite changed settings.

No books, Amazon dictionary databases, private preferences, device logs, catalog databases or firmware files are distributed. Keep diagnostic exports and generated case scripts private. Original helper code and documentation use the MIT License; upstream tools retain their own licenses.
