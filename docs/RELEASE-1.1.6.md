# Gamble Game 1.1.6

Eighth release. The quality-of-life pass: search the lobby, jump back to your last bet,
keep dated backups of your saves and watch your profit curve. No rules changed and no
content was removed - everything new sits beside what was already there.

## What's new since 1.1.5

**Search the lobby** - a search box now sits above the game grid. Type a few letters and
only the matching games stay visible (name, subtitle or the game's own key all count);
whole categories hide when nothing in them matches, and clearing the box brings everything
back. Esc clears the search first, then leaves the box.

**Recently played** - above the search box a new row shows the last five games you
played, newest on the left, in the same style as the category buttons. Clicking one
starts it right away. The row is stored in your save file (`x:recents` line), so it
survives restarts; old saves simply start with an empty row.

**Repeat last bet** - after any finished round the bet bar grows a "Repeat last bet"
button showing your last wager in the tooltip. One click puts that exact amount back
into the bet box (clamped to what you can actually bet right now). The button only
appears once you have a last bet to repeat.

**Save backups** - Settings now has a SAVE BACKUPS section with a manager: one click
zips `savegame.txt`, `gamble_meta.txt`, `gamble_settings.txt` and your shared result
cards into `backups\backup-YYYYMMDD-HHMMSS.zip` next to the game. The dialog lists the
newest backups first and lets you restore one over the current files (with a
confirmation) or delete it. A restore reloads the run, the meta and the settings into
the live window immediately - no restart needed. The `backups\` folder is never
committed or shipped.

**Profit over the last rounds** - the Statistics page gained a second chart under the
net worth curve: your cumulative profit across the last rounds, one point per round, so
a hot or cold streak is visible as a slope instead of a number. Like everything else it
fills in as you play.

**A quick tour on the very first run** - instead of the full help page, a new run now
opens a five-step tour: what the goal is, what the left bar means, how to pick a game
and set a bet, what the side bets and menus are, and where the rules live (F1). Back,
Skip and Next at your own pace; the full help page is still one click away in the lobby
and on F1.

Old saves and old meta files load unchanged; the new save lines default sensibly
(no last bet, no recents).

## Installing

| File | What it is |
|---|---|
| `GambleGame-1.1.6-Setup.exe` | Installer. No admin rights needed, installs to `%LOCALAPPDATA%\Programs\Gamble Game`. Uninstalling keeps your saves. |
| `GambleGame-1.1.6-win64.zip` | Portable. Unpack it and double-click `GambleGame.exe`. Keep the `_internal` folder next to it. |

No Python, no PyQt6, nothing to install besides the game itself. Windows 10/11, 64-bit.

Your progress lives in three files next to the exe - `savegame.txt`, `gamble_meta.txt`,
`gamble_settings.txt`. Copy those three to move your progress to another machine, or use
the new backup manager to zip them in one click. Shared result cards land in `share\`
and can be deleted freely.
`OKUMA-BENIM.txt` inside both packages is the short Turkish version of these instructions.

## Verifying the files

```
0A08F623429DF0EAF300F2D8CC86B88BC004F55B6E83209B763AB32219F8FB42  GambleGame-1.1.6-win64.zip
0D961C038EC2FE6E2A3FD25120DCDC8D924EA5CCB3B853DEBDD90B06B9FC5663  GambleGame-1.1.6-Setup.exe
```

PowerShell: `Get-FileHash .\GambleGame-1.1.6-Setup.exe -Algorithm SHA256`

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
