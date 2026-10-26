"""All game pages. GAMES maps the game key to its page class."""
from .basic import CoinGame, DiceGame, ScratchGame, SlotGame, WheelGame
from .crash import CrashGame
from .hilo import HiLoGame
from .mines import MinesGame
from .plinko import PlinkoGame
from .table import BaccaratGame, BlackjackGame, LottoGame, PokerGame, RaceGame, RouletteGame

GAMES = {
    'coin': CoinGame, 'dice': DiceGame, 'roulette': RouletteGame, 'blackjack': BlackjackGame,
    'slot': SlotGame, 'tombala': LottoGame, 'poker': PokerGame, 'baccarat': BaccaratGame,
    'race': RaceGame, 'wheel': WheelGame, 'scratch': ScratchGame, 'crash': CrashGame, 'plinko': PlinkoGame,
    'hilo': HiLoGame, 'mines': MinesGame,
}
