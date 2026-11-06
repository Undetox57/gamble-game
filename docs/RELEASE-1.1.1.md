# Gamble Game 1.1.1

Third release. A foundation pass: the parts of the interface Windows was still drawing in its own
light style are now part of the game's look, and the main refresh loop stops doing work nobody can
see. No rules changed, no content added - everything just looks and feels tighter.

## What's new since 1.1.0

**Every control is styled now** - spin boxes (wallet, bank, bet) get dark buttons with gold
drop-down arrows, combo boxes in Settings get a matching drop-down, right-click menus (log, spin
box, table) open dark with gold selection instead of a white Windows box, disabled controls dim
properly, and the statistics table's corner button, the scroll-area corner and message-box buttons
all match the theme. Every colour comes from the active theme, so a theme swap repaints them too.

**The refresh loop got quieter** - `refresh()` runs after every action and used to re-set dozens of
labels, buttons and panels even when nothing had changed. It now detects unchanged text and
stylesheets and leaves them alone; the Bank page and the Help page skip their rebuild entirely when
their inputs have not moved. Long sessions feel smoother, especially with the message log open.

**The message log is a tail** - it keeps the last 500 lines instead of growing forever, so a very
long session no longer slows the document down.

**The wallet roll is back** - the animated count-up on the wallet number (added in 1.0.x) had
silently stopped working: the refresh loop captured the "before" value too early, so the animation
always had nothing to roll from. It rolls again, and a second change caught mid-roll continues from
the number actually on screen.

**Settings stopped restyling the app for nothing** - changing any single setting used to rebuild
and re-apply the whole application stylesheet, re-polishing every widget. Identical stylesheets are
now skipped, so a checkbox flip restyles once, and only when it really changed something.

Old saves and old meta files load unchanged; there is nothing new to store.

## Installing

| File | What it is |
|---|---|
| `GambleGame-1.1.1-Setup.exe` | Installer. No admin rights needed, installs to `%LOCALAPPDATA%\Programs\Gamble Game`. Uninstalling keeps your saves. |
| `GambleGame-1.1.1-win64.zip` | Portable. Unpack it and double-click `GambleGame.exe`. Keep the `_internal` folder next to it. |

No Python, no PyQt6, nothing to install besides the game itself. Windows 10/11, 64-bit.

Your progress lives in three files next to the exe - `savegame.txt`, `gamble_meta.txt`,
`gamble_settings.txt`. Copy those three to move your progress to another machine. Shared result
cards land in `share\` and can be deleted freely.
`OKUMA-BENIM.txt` inside both packages is the short Turkish version of these instructions.

## Verifying the files

```
25F744C13A6B6A61A18C8F5A9262C63948B1BD864CE8D2BD43EAA1B5A820CE9C  GambleGame-1.1.1-win64.zip
C41C2D31F11363E50A76EBD9A34052CDAC68BA07CF81292CF0EEFA8E18AEF33F  GambleGame-1.1.1-Setup.exe
```

PowerShell: `Get-FileHash .\GambleGame-1.1.1-Setup.exe -Algorithm SHA256`

## SmartScreen and antivirus

The executables are not code-signed, so Windows may show "Unknown publisher" on first run:
click **More info -> Run anyway**. If an antivirus deletes the file, it is a false positive -
the exe is built with PyInstaller, which unpacks itself at runtime and looks suspicious to
heuristics. Paste the SHA-256 above into virustotal.com to see 70+ engines scan it, and report the
false positive using the templates in `docs/YAYINLAMA.md`.

## Source

MIT licensed. The game logic (`gamble/rules.py`, `gamble/engine.py`) has no Qt in it, which is
why the simulator and the GUI always play by the same rules.

Build from source:

```
pip install PyQt6
python gamble_gui.py
```

40 unit tests: `python -m unittest discover -s tests`
Return-to-player of every game: `python simulate.py rtp`
