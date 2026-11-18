# Gamble Game 1.1.5

Seventh release. The infrastructure pass: a lint gate and a CI pipeline that now guard every
push, and a silent in-app update check that tells you in the lobby when a newer release exists.
No rules changed, no content added, and nothing looks different until there actually is an
update to announce.

## What's new since 1.1.4

**A lint gate over the whole code base** - `ruff.toml` pins a classic rule set (pyflakes plus the
basic pycodestyle checks) and `python -m ruff check gamble simulate.py tests tools` now passes
clean. Fixing the 26 findings uncovered one real latent bug: in `retranslate()` a local variable
named `current` shadowed the imported i18n `current()`, so switching the interface language
while a round was running would have raised `UnboundLocalError`. The rest were unused imports
and variables, ambiguous names and test lines packed with semicolons.

**Continuous integration** - `.github/workflows/ci.yml` runs byte-compilation, the lint gate,
all 40 unit tests and the Turkish translation check on every push and pull request
(Python 3.11). A regression now fails the build instead of reaching a release. The translation
check itself moved into the repo as `tools/i18n_check.py`; it derives its root from its own
location and exits non-zero when a key is missing, so CI can act on it.

**In-app update check** - at startup the game asks GitHub for the newest release in a
background thread (4 second timeout) and compares it against `config.VERSION`. If a newer
version exists, a gold pill appears at the top of the lobby: "Update available: 1.1.6" - click
it and the releases page opens in your browser. Everything else about it is deliberately
quiet: it runs behind a new setting (**Settings -> Check for updates on startup**, on by
default), it never blocks or delays the game, and any failure - offline, firewalled, rate
limited - stays completely silent. Old settings files simply load with the default; nothing to
migrate.

Old saves and old meta files load unchanged; the update check stores nothing.

## Installing

| File | What it is |
|---|---|
| `GambleGame-1.1.5-Setup.exe` | Installer. No admin rights needed, installs to `%LOCALAPPDATA%\Programs\Gamble Game`. Uninstalling keeps your saves. |
| `GambleGame-1.1.5-win64.zip` | Portable. Unpack it and double-click `GambleGame.exe`. Keep the `_internal` folder next to it. |

No Python, no PyQt6, nothing to install besides the game itself. Windows 10/11, 64-bit.

Your progress lives in three files next to the exe - `savegame.txt`, `gamble_meta.txt`,
`gamble_settings.txt`. Copy those three to move your progress to another machine. Shared result
cards land in `share\` and can be deleted freely.
`OKUMA-BENIM.txt` inside both packages is the short Turkish version of these instructions.

## Verifying the files

```
66C341110FEAEA1B411F735117A97511DB82C15DB12A74862DFA7C4717051CDC  GambleGame-1.1.5-win64.zip
78FD032EF3590CEA75505342F65CB70A693E46CCB4784504A7886F671F082D92  GambleGame-1.1.5-Setup.exe
```

PowerShell: `Get-FileHash .\GambleGame-1.1.5-Setup.exe -Algorithm SHA256`

## SmartScreen and antivirus

The executables are not code-signed, so Windows may show "Unknown publisher" on first run:
click **More info -> Run anyway**. If an antivirus deletes the file, it is a false positive -
the exe is built with PyInstaller, which unpacks itself at runtime and looks suspicious to
heuristics. Paste the SHA-256 above into virustotal.com to see 70+ engines scan it, and report
the false positive using the templates in `docs/YAYINLAMA.md`.

## Source

MIT licensed. The game logic (`gamble/rules.py`, `gamble/engine.py`) has no Qt in it, which is
why the simulator and the GUI always play by the same rules.

Build from source:

```
pip install PyQt6
python gamble_gui.py
```

40 unit tests: `python -m unittest discover -s tests`
Lint gate: `python -m ruff check gamble simulate.py tests tools`
Translation check: `python tools/i18n_check.py`
Return-to-player of every game: `python simulate.py rtp`
