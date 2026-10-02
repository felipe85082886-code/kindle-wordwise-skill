# Production workflow

Use official [Calibre](https://calibre-ebook.com/download) and [WordDumb](https://github.com/xxyzz/WordDumb). Check current [installation](https://xxyzz.github.io/WordDumb/installation.html) and [usage](https://xxyzz.github.io/WordDumb/usage.html) docs when installing or resolving version differences. The confirmed case used Calibre 9.15.0 and WordDumb 3.36.0; these are evidence, not required versions. Neither is bundled here.

## Tools and source

Discover executables on PATH or in installed application bundles. On macOS tools commonly live in `calibre.app/Contents/MacOS/`; Windows exposes `.exe` tools. Use an isolated `CALIBRE_CONFIG_DIRECTORY` for independent pipelines. Temporary tools may support one job but must not become hardcoded dependencies of this skill. Respect existing network/proxy settings. Install reputable upstream dependencies within authorized scope, with a durable location for repeat work.

Check actual book metadata rather than trusting the filename. Correct title/author/language in a working copy. Preserve the edition's cover. Inspect images after conversion and compare the English text sequence between source and reconstructed output, investigating differences beyond layout normalization.

Example after checking metadata:

```sh
ebook-convert source.epub final.azw3 --output-profile tablet --title 'Book Title' --authors 'Author' --language en --cover cover.jpg
```

The tablet profile helped preserve images in the case; it is not required for every book. Do not insert soft hyphens. WordDumb may change ASIN metadata, so inspect the final book **after** annotation generation.

## Native Chinese glosses

The reader selects a native dictionary according to its chosen language. The confirmed device used `/mnt/us/system/kll/kll.en.zh.klld` and `targetLang=zh`. Native English sense IDs used by WordDumb also existed in the Chinese dictionary, verified against every generated row. Sidecar metadata still described English dictionary data (`targetLanguages=en`); the device setting selected Chinese display.

Use WordDumb's native Amazon sense-ID mode and verify the actual dictionary. Do not mechanically edit sidecar language fields. Preserve the existing native dictionary by leaving **Use Wiktionary definition** disabled; upstream states that enabling it replaces the Chinese database. Follow current upstream UI choices for the requested language.

Do not fabricate an English-labelled copy of Chinese dictionary data: it failed in the case and was rolled back. Missing English dictionary data alone did not establish the failure when Chinese was selected and valid. If the intended native dictionary is absent, prefer a normal supported device download; do not redistribute someone else's Amazon database. A different dictionary source must match the user's request.

## Generate and inspect

Calibre's ordinary **Send to device** does not send WordDumb sidecars. Use WordDumb's sending function or manually merge a verified package over USB. Upstream states generated Word Wise does not work for amazon.cn accounts; check account region when relevant.

For delegated CLI operation inspect available arguments:

```sh
calibre-debug -r WordDumb -- -h
```

Use the installed version's documented flags for Word Wise and avoid unwanted X-Ray generation. Do not assume a flag set from another version. Preserve the final modified book with its own annotations.

Read-only inspection with Python 3.10+:

```sh
python3 scripts/inspect_package.py --book final.azw3 --dictionary /path/to/kll.en.zh.klld --output inspection.json
```

`--layer` overrides sidecar discovery. Omitting `--dictionary` means sense-ID compatibility has not been checked. The inspector verifies standalone KF8 identity, English locale, EBOK type, ASIN/file name, ACR/revision, SQLite integrity, ranges and difficulty. It rejects DRM and combined MOBI instead of guessing.

For exact byte-offset verification:

```sh
calibre-debug -e scripts/extract_kf8.py -- final.azw3 reconstructed.bin
python3 scripts/inspect_package.py --book final.azw3 --raw-html reconstructed.bin --dictionary /path/to/kll.en.zh.klld --output inspection.json
```

The extractor uses Calibre internal APIs, which may change. Fail visibly and adapt if needed. Use explicit checks rather than `assert` inside Calibre's optimized Python.

## Cover and USB layout

```text
Kindle_USB/
  documents/
    Book - Author.azw3
    Book - Author.sdr/
      LanguageLayer.en.BXXXXXXXXX.kll
  system/thumbnails/
    thumbnail_BXXXXXXXXX_EBOK_portrait.jpg
  amazon-cover-bug/
    thumbnail_BXXXXXXXXX_EBOK_portrait.jpg
```

`make_cover.py` creates both JPEGs from supplied artwork; Pillow is optional for this helper. Keep aspect ratio inside a 374 × 500 bounding box. The second path mirrors Calibre's recovery-cache convention; it does not guarantee visible refresh on every firmware.

Before updating an existing book, back up its exact book, `.sdr` reading records and thumbnail. Preserve existing identity when possible; a regenerated identity can create a duplicate and break reading continuity. Do not resend a cloud document as an assumed cover fix. If catalog association is missing, use a specifically available cover-repair workflow; do not edit the catalog blindly.

Merge individual intended files into existing device folders and verify hashes. On macOS `COPYFILE_DISABLE=1` avoids AppleDouble `._` files that can be mistaken for SQLite databases. This matched-sidecar workflow uses USB: Send to Kindle conversion can change identity and does not preserve local sidecar attachment.

Eject safely and inspect the exact title/author in body text. A cloud copy may have a different identity. Check actual library cover and native hints separately.
