# Gamble Game 1.0.0

First public release. A casino-life simulation built with PyQt6: work, gamble, borrow,
level up, and try to reach your goal - or find another way out.

## What's in it

**16 games, all priced at ~92% return-to-player**
Coin Flip, Dice, Roulette, Blackjack, Slot, Lotto, Poker, Baccarat, Race, Wheel of Fortune,
Scratch Card, Crash, Plinko, Hi-Lo, Mines and **Keno** (new: pick 10 of 40, exact 90.05% RTP,
`Alt+6`).

**Two ways to change the stakes**
- **Loan shark (Tefeci)** - no credit check, but 6% a day, a hard 4-day deadline and a collector who
  takes a quarter of your wallet. The one favour: while you owe him he cleans 15% extra out of every win.
  Owe him three times your ceiling and the run ends.
- **Tournament (Turnuva)** - a fixed 1,000 TL entry held for a 10-day race against your own net worth.
  Finish ahead and you get the entry back plus 5% of the growth; finish behind and it is gone.
  Best result per difficulty is kept forever.

**The rest of the life sim**
Jobs with tenure ranks, loans and bank interest, shop items, random events, a streak side bet,
achievements, six endings, per-difficulty records and a leaderboard, session summaries,
themes, sound and rebindable keys.

**Tools**
- `simulate.py` - measures the real return-to-player of every game and plays whole runs with bots
- 35 unit tests: `python -m unittest discover -s tests`

## Installing

| File | What it is |
|---|---|
| `GambleGame-1.0.0-Setup.exe` | Installer. No admin rights needed, installs to `%LOCALAPPDATA%\Programs\Gamble Game`. Uninstalling keeps your saves. |
| `GambleGame-1.0.0-win64.zip` | Portable. Unpack it and double-click `GambleGame.exe`. Keep the `_internal` folder next to it. |

No Python, no PyQt6, nothing to install besides the game itself. Windows 10/11, 64-bit.

Your progress lives in three files next to the exe - `savegame.txt`, `gamble_meta.txt`,
`gamble_settings.txt`. Copy those three to move your progress to another machine.
`OKUMA-BENIM.txt` inside both packages is the short Turkish version of these instructions.

## Verifying the files

```
1E7C366B8228C304EBD0BC3BF7DACC610FB6FFE08AC14B0C4344FEF46D94AE94  GambleGame-1.0.0-win64.zip
6F551B68F528B4059DF76E55501A7EF4225B8CC91084209B7381EF6FFC5A3A21  GambleGame-1.0.0-Setup.exe
```

PowerShell: `Get-FileHash .\GambleGame-1.0.0-Setup.exe -Algorithm SHA256`

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
