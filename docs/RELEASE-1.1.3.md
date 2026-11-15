# Gamble Game 1.1.3

Fifth release. The rich-graphics pass: every playing card on the table is now drawn as a real
card, the tables themselves have texture behind them, and the parts of the interface that still
looked flat got proper panels. No rules changed, no content added.

## What's new since 1.1.2

**Real playing cards** - every card in the game (blackjack, poker, baccarat, Hi-Lo, the
computer's hands) is now painted instead of being styled text: a white gradient body with a
soft drop shadow under its bottom-right corner, the rank and suit centred, and a tiny suit pip
in each corner. The face-down back is navy with a white frame, a fine diagonal lattice and a
star emblem in a ring. The cards you mark for a change in Poker get a gold frame, and the
"Card size" setting now reaches the Poker hand too.

**Texture on the felt** - every game table carries a very faint field of oversized suit glyphs
(spades and clubs in white, hearts and diamonds in soft red), like the watermark on a real
casino table. It sits behind everything, never intercepts a click, follows every window resize,
and is only created when **Visual effects** is on.

**A panel for the chart** - the net-worth chart on the Statistics page sits on a themed dark
panel with a border and rounded corners instead of a flat painted-on black box, so it reads as
part of the page in every theme.

**Pill section headers** - every section header (WALLET, LEVEL, MENTAL HEALTH, GOAL, the game
categories, the page headers) is now a dark pill with gold text rather than a bare grey caption,
which makes the side panel and every page easier to scan.

**Confetti got variety** - a burst now mixes three shapes: the classic streamer, round dots
and little casino chips with a white ring. Same gating as before: only with Visual effects on.

Every one of these lives in the drawing layer only - the rules, the engine and the payouts are
untouched, and the return-to-player of every game is bit-for-bit the same as in 1.1.2.

Old saves and old meta files load unchanged; there is nothing new to store.

## Installing

| File | What it is |
|---|---|
| `GambleGame-1.1.3-Setup.exe` | Installer. No admin rights needed, installs to `%LOCALAPPDATA%\Programs\Gamble Game`. Uninstalling keeps your saves. |
| `GambleGame-1.1.3-win64.zip` | Portable. Unpack it and double-click `GambleGame.exe`. Keep the `_internal` folder next to it. |

No Python, no PyQt6, nothing to install besides the game itself. Windows 10/11, 64-bit.

Your progress lives in three files next to the exe - `savegame.txt`, `gamble_meta.txt`,
`gamble_settings.txt`. Copy those three to move your progress to another machine. Shared result
cards land in `share\` and can be deleted freely.
`OKUMA-BENIM.txt` inside both packages is the short Turkish version of these instructions.

## Verifying the files

```
749975B71083EC26DB18B5DD60FC4531D6C666E2A80890545C399A9ABF24CE57  GambleGame-1.1.3-win64.zip
EEF0F70AC0BC39122155578EC26878B8F710B314890F58C6DB9CA1A3310CDFAF  GambleGame-1.1.3-Setup.exe
```

PowerShell: `Get-FileHash .\GambleGame-1.1.3-Setup.exe -Algorithm SHA256`

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
Return-to-player of every game: `python simulate.py rtp`
