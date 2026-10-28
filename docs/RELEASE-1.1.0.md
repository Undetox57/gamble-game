# Gamble Game 1.1.0

Second release. Everything from 1.0.0 plus four new ways to play with a run and a full second
interface language.

## What's new since 1.0.0

**Turkish interface** - the whole UI, the settings and both rule books are English or Turkish,
switchable at any time in Settings (it is applied the moment the dialog closes). Game data (event
text, engine messages) stays in English.

**Result card** - one click (Statistics page, or the session summary when you quit) saves a 1200x630
PNG of your run - wallet, level, day, goal percentage - into the `share` folder next to the exe, and
copies it to the clipboard. Ready to post anywhere.

**Trophy room** - a new page with all 36 achievements in one case plus record plaques: best net
worth, best tournament, best sprint, deepest goal chain, endings found, best win of this run.

**Sprint tournament** - a second, much shorter tournament beside the 10-day classic: 3 days,
250 TL entry, 10% of your growth back (capped at 600 TL), 15 exp. It keeps its own record per
difficulty, and only one tournament window can run at a time.

**The goal chain** - reaching the money goal still ends the run, but it now opens the next rung.
Every difficulty keeps its own chain of five rungs; on Normal the goal climbs
50,000 → 75,000 → 150,000 → 300,000 → 1,000,000 TL. A cleared rung queues an exp reward that your
next run collects at startup, and the unlocked rung is stored in the meta file forever. The chain
is drawn under the goal bar in the side panel.

**Fixes** - clean-day farming (the counter only moves on real days), the in-round navigation lock
(a keyboard shortcut could drop a hand that was still on the table), save robustness (one bad line
no longer costs a run), and payout edge cases.

Old saves load unchanged: a save without the new lines starts the chain at rung 1 (the classic
goal), plays the classic tournament, and keeps every achievement, ending and record.

## Installing

| File | What it is |
|---|---|
| `GambleGame-1.1.0-Setup.exe` | Installer. No admin rights needed, installs to `%LOCALAPPDATA%\Programs\Gamble Game`. Uninstalling keeps your saves. |
| `GambleGame-1.1.0-win64.zip` | Portable. Unpack it and double-click `GambleGame.exe`. Keep the `_internal` folder next to it. |

No Python, no PyQt6, nothing to install besides the game itself. Windows 10/11, 64-bit.

Your progress lives in three files next to the exe - `savegame.txt`, `gamble_meta.txt`,
`gamble_settings.txt`. Copy those three to move your progress to another machine. Shared result
cards land in `share\` and can be deleted freely.
`OKUMA-BENIM.txt` inside both packages is the short Turkish version of these instructions.

## Verifying the files

```
5D8E929354509BEAFCDAEE693451A585E9DA2BC6DB7E1A8E31EB85E65F1A6500  GambleGame-1.1.0-win64.zip
46F285DCCD40278E6B8FDBC38084FA3090BCF3D17A477D938865E5910B1BF4FE  GambleGame-1.1.0-Setup.exe
```

PowerShell: `Get-FileHash .\GambleGame-1.1.0-Setup.exe -Algorithm SHA256`

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

38 unit tests: `python -m unittest discover -s tests`
Return-to-player of every game: `python simulate.py rtp`
