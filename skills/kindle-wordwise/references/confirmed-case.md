# Confirmed case and limits

Tested on **Kindle Paperwhite 5 (11th generation), firmware 5.19.2**, with an English standalone AZW3 and native Chinese Word Wise dictionary. A functioning SH Integration launcher already existed; this project did not install a jailbreak.

The package had matching ASIN/ACR/revision, device SQLite integrity `ok`, and **7,016** annotations. Every referenced native English sense ID existed in the Chinese dictionary. Exported settings confirmed `isEnabled=true` and `targetLang=zh`; `ftuxShown` was absent. The bottom-right area showed reading percentage, with no Word Wise entry.

The updated menu logged that in-book dialog migration was enabled and the tutorial was skipped. Local reader inspection showed a false default for `ftuxShown` and a handler path gated on first-use state. Appending only `ftuxShown=true`, followed by a **manual restart**, made Chinese glosses appear, confirmed by the user. Automatic restart did not occur. This establishes one device/firmware case; other firmware is unconfirmed.

An English-labelled Chinese dictionary copy was tested, failed and was rolled back. It is not the reusable solution. Existing ASIN-keyed cover files were separately repaired, but visible cover recovery was not confirmed when this reference was written; do not claim universal cover success.

No book text, Amazon dictionary, preferences, catalog, logs or firmware code is distributed. Helper code and synthetic tests are original.

Upstream: [WordDumb source](https://github.com/xxyzz/WordDumb), [usage](https://xxyzz.github.io/WordDumb/usage.html), [installation](https://xxyzz.github.io/WordDumb/installation.html), [Calibre](https://calibre-ebook.com/download), [SH Integration scriptlets](https://kindlemodding.org/kindle-dev/scriptlets.html). The launcher link explains existing access; it is not a routine-install instruction.
