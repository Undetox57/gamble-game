# Gamble Game 1.1.2

Fourth release. The game moves now: pages arrive instead of cutting in, the meters glide to
their new values, and the day announces itself. No rules changed, no content added.

## What's new since 1.1.1

**Pages fade in** - every navigation (lobby, bank, statistics, jobs, achievements, shop, trophy
room, help and the game tables) now fades in with a short rise instead of cutting in hard. The
effect lasts about a fifth of a second, is removed from the widget the moment it ends, and is
cancelled cleanly when you navigate again mid-fade or switch language mid-fade.

**The meters glide** - the four progress bars in the side panel (experience, mental health, work
streak, goal) animate to their new value instead of snapping there, so a win, a loss or a day at
work reads as a movement rather than a jump. When the bar's scale itself changes (a level-up, a
new goal rung) the value snaps instead: a glide across different scales would be meaningless.

**The day pops** - when a new day starts, the day label in the side panel fades up from near
transparent, so the turn of time is visible without stealing attention from the panel.

Every one of these is gated behind **Visual effects** in Settings and respects **Animation
speed** (Instant turns all of them off, exactly like before). Turning the effects off mid-glide
lands every bar on its target at once.

Old saves and old meta files load unchanged; there is nothing new to store.

## Installing

| File | What it is |
|---|---|
| `GambleGame-1.1.2-Setup.exe` | Installer. No admin rights needed, installs to `%LOCALAPPDATA%\Programs\Gamble Game`. Uninstalling keeps your saves. |
| `GambleGame-1.1.2-win64.zip` | Portable. Unpack it and double-click `GambleGame.exe`. Keep the `_internal` folder next to it. |

No Python, no PyQt6, nothing to install besides the game itself. Windows 10/11, 64-bit.

Your progress lives in three files next to the exe - `savegame.txt`, `gamble_meta.txt`,
`gamble_settings.txt`. Copy those three to move your progress to another machine. Shared result
cards land in `share\` and can be deleted freely.
`OKUMA-BENIM.txt` inside both packages is the short Turkish version of these instructions.

## Verifying the files

```
8CB32402748E68A1D7F6476517858B33AAECDB3854C2B8764BE40C90FAA4C68A  GambleGame-1.1.2-win64.zip
7A6354BEFDC65C5AC6FB5925809B07E6790A67FF5FF3FD0EEFE44F196BA69D07  GambleGame-1.1.2-Setup.exe
```

PowerShell: `Get-FileHash .\GambleGame-1.1.2-Setup.exe -Algorithm SHA256`

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
