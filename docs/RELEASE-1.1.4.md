# Gamble Game 1.1.4

Sixth release. The frame-rate pass: the wheel, the plinko board and the horse track now paint
their heavy background art once into memory and blit it, so animations run on a fraction of the
former drawing cost. No rules changed, no content added, and nothing looks different.

## What's new since 1.1.3

**The wheel spins from a cached disc** - the twelve slices, their labels and the outer rim are
painted once at 2x resolution into an off-screen pixmap, then drawn rotated as a single image
per frame. Before, every frame redrew twelve pie slices with individual outlines and twelve
rotated text labels. The pointer hub, the glow on the slice passing under the pointer and the
gold ring around the winning slice are still painted live on top, so all feedback is unchanged.

**The plinko board caches its payout slots** - the nine slot columns are painted once per risk
level (low / medium / high have different multipliers, so the cache is keyed by risk) and
redrawn only when the risk changes or the board is resized. The pegs stay live so a struck peg
still glows over the felt, and the winning slot pops exactly as before.

**The horse track caches its scenery in two layers** - the background (sky, turf, rails, crowd)
is one cached image and the five name plates another, both keyed by size and screen scale.
The layers are blitted in the original order, so the start gate still rises from *behind* the
plates, and the running horses, their dust and the finish-line checks stay live.

**A rotation bug found while verifying** - the new wheel code initially applied the spin angle
twice to the live overlays (the slice under the pointer and the gold winning ring sat at the
wrong angle while the wheel was turning, and the hub gradient rotated with the wheel). Caught
by a pixel-by-pixel comparison against the old painter at several angles, fixed with a single
un-rotate line. At rest the bug was invisible; only a moving wheel showed it.

Every change lives in the drawing layer only - the rules, the engine and the payouts are
untouched, and the return-to-player of every game is bit-for-bit the same as in 1.1.3. The
caches are performance, not effects: turning **Visual effects** off renders the identical
pixels.

Old saves and old meta files load unchanged; there is nothing new to store.

## Installing

| File | What it is |
|---|---|
| `GambleGame-1.1.4-Setup.exe` | Installer. No admin rights needed, installs to `%LOCALAPPDATA%\Programs\Gamble Game`. Uninstalling keeps your saves. |
| `GambleGame-1.1.4-win64.zip` | Portable. Unpack it and double-click `GambleGame.exe`. Keep the `_internal` folder next to it. |

No Python, no PyQt6, nothing to install besides the game itself. Windows 10/11, 64-bit.

Your progress lives in three files next to the exe - `savegame.txt`, `gamble_meta.txt`,
`gamble_settings.txt`. Copy those three to move your progress to another machine. Shared result
cards land in `share\` and can be deleted freely.
`OKUMA-BENIM.txt` inside both packages is the short Turkish version of these instructions.

## Verifying the files

```
CEA4DC490C33F55E2D2B6F64694FA08AE6FBEED02969842265B0E02C541516DE  GambleGame-1.1.4-win64.zip
D4D2088B7F1731D6F39D55CE04A7FE876EFB0284D90F3569E418DBE93AC1BD72  GambleGame-1.1.4-Setup.exe
```

PowerShell: `Get-FileHash .\GambleGame-1.1.4-Setup.exe -Algorithm SHA256`

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
