# Gamble Game 1.1.7

Ninth release. The audio/visual pass: opt-in background music and your wins arriving on a
casino chip. No rules changed and no content was removed - everything new sits beside what
was already there.

## What's new since 1.1.6

**Background music (opt-in)** - Settings gained a new "Background music" checkbox. Tick it
and the game plays a slow, synthesised loop (a warm I-vi-IV-V pad with a soft arpeggio,
about 24 seconds per round) that fades to silence at the seam so it repeats without a click.
Like the sound effects, no audio files ship with the game: the loop is generated the first
time you switch it on and cached in your temp folder. It is completely separate from the
"Sound effects" toggle - you can have one, the other, both or neither. **It is off by
default**; old settings files simply keep it off until you ask for it.

**Wins arrive on a chip** - the floating result that pops up after every round now rides in
on a casino chip: a round chip with a shaded gradient body, a dark rim and the amount in
ink, which pops, rises and drifts away. It uses the colour of the result (green for a win,
red for a loss) and obeys the same switches as before - turn off visual effects or set
animation speed to off and it stays away.

Old saves and old settings files load unchanged; the new music setting defaults to off.

## Installing

| File | What it is |
|---|---|
| `GambleGame-1.1.7-Setup.exe` | Installer. No admin rights needed, installs to `%LOCALAPPDATA%\Programs\Gamble Game`. Uninstalling keeps your saves. |
| `GambleGame-1.1.7-win64.zip` | Portable. Unpack it and double-click `GambleGame.exe`. Keep the `_internal` folder next to it. |

No Python, no PyQt6, nothing to install besides the game itself. Windows 10/11, 64-bit.

Your progress lives in three files next to the exe - `savegame.txt`, `gamble_meta.txt`,
`gamble_settings.txt`. Copy those three to move your progress to another machine, or use
the backup manager in Settings to zip them in one click. Shared result cards land in
`share\` and can be deleted freely.
`OKUMA-BENIM.txt` inside both packages is the short Turkish version of these instructions.

## Verifying the files

```
39D84B416C40282384083C5FC2BBD73B9DB751DCE0D9A389ADB678EC1DB58A7E  GambleGame-1.1.7-win64.zip
A7C0B91B6FDDED84C265F3BF396F3346618695033CB19A60996BBAFC4EE6A023  GambleGame-1.1.7-Setup.exe
```

PowerShell: `Get-FileHash .\GambleGame-1.1.7-Setup.exe -Algorithm SHA256`

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
