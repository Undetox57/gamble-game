# Gamble Game

A casino-life simulation: work, gamble, borrow, level up, and try to reach your goal (or find another way out).

    pip install PyQt6
    python gamble_gui.py

## Moving from the old single-file version
Copy your `savegame.txt` (and `gamble_meta.txt`, `gamble_settings.txt` if you have them) into this folder,
next to `gamble_gui.py`. Old saves load fine; the console version can still read the new save files.

## Layout
    gamble_gui.py        starts the game
    simulate.py          balance simulator (no GUI needed)
    gamble/
      config.py          ALL the numbers: levels, jobs, shop items, difficulties, achievements, endings
      rules.py           pure game maths (payouts, hands, crash point, plinko tables). No Qt.
      state.py           GameState / MetaState and the save files
      engine.py          economy and daily life (work, loans, shop, endings). No Qt.
      events.py          the random events
      style.py           stylesheet, themes, display settings
      widgets.py         shared widgets (cards, chart, confetti)
      games/             one page per game (base.py, basic.py, table.py, crash.py, plinko.py, hilo.py, mines.py)
      pages.py           bank, jobs, shop, achievements, statistics, how to play
      dialogs.py         events, endings, settings, new game
      window.py          main window, navigation, keyboard shortcuts
    tests/test_core.py   python -m unittest discover -s tests

Because the rules and the engine have no Qt in them, the simulator and the GUI always play by the same rules.

## Balance simulator
    python simulate.py rtp                 return-to-player of every game (100% = fair, lower = the house wins)
    python simulate.py run                 full runs with 4 kinds of bots on every difficulty
    python simulate.py run --difficulty hard --bots gambler,worker --runs 500 --days 800

To change the economy, edit the numbers in `gamble/config.py` or the payout tables at the top of
`gamble/rules.py`, then run the simulator again.

## Keyboard
Lobby: 1-9 and 0, then Alt+1..5 start the games (the key is shown on each button), W work, D pass day,
O go out, B bank, J jobs, S shop, T statistics, A achievements, P settings, H or F1 help.
In a game the keys are written on the buttons; Space usually does the main thing.
Esc goes back, F11 toggles fullscreen, Ctrl+Q quits.
