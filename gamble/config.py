"""Static game data: files, games, levels, jobs, shop items, difficulties, achievements and endings.

No Qt in here, so the balance simulator can import it too.
"""
import os
import sys

# Files live next to gamble_gui.py (or next to the .exe once packaged). Always read these as
# `config.SAVE_FILE` (not `from ... import`) so tests can point them somewhere else.
def _base_dir():
    if getattr(sys, 'frozen', False):
        # PyInstaller onefile: __file__ points into the temporary _MEIxxxx folder, which is
        # wiped on exit - the saves must live beside the executable instead.
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


BASE_DIR = _base_dir()
SAVE_FILE = os.path.join(BASE_DIR, 'savegame.txt')
META_FILE = os.path.join(BASE_DIR, 'gamble_meta.txt')
SETTINGS_FILE = os.path.join(BASE_DIR, 'gamble_settings.txt')

# ---------------------------------------------------------------- games
GAME_KEYS = ['coin', 'dice', 'roulette', 'blackjack', 'slot', 'tombala', 'poker', 'baccarat', 'race',
             'wheel', 'scratch', 'crash', 'plinko', 'hilo', 'mines', 'keno']
GAME_NAMES = {'coin': 'Coin Flip', 'dice': 'Dice Roll', 'roulette': 'Roulette', 'blackjack': 'Blackjack',
              'slot': 'Slot Machine', 'tombala': 'Lotto', 'poker': 'Poker', 'baccarat': 'Baccarat',
              'race': 'Race Bet', 'wheel': 'Wheel of Fortune', 'scratch': 'Scratch Card',
              'crash': 'Crash', 'plinko': 'Plinko', 'hilo': 'Hi-Lo', 'mines': 'Mines', 'keno': 'Keno'}
GAME_SUBTITLES = {
    'coin': '50/50 • pays 2×', 'dice': 'Guess 1-6 • pays 5×', 'slot': 'Match 3 → 5× • 2 → 1.5×',
    'roulette': 'Color 2× • number bonus', 'blackjack': 'Beat the dealer • 2.5×', 'poker': '5-card draw • pays 1.9×',
    'tombala': 'Pick 6/30 • up to 2000×', 'wheel': 'Spin • 0× to 4×', 'scratch': 'Match 3 • up to 10×',
    'race': 'Pick the winner • 4×', 'baccarat': 'Player vs Banker • 1.9×',
    'plinko': 'Drop a ball • up to 20×', 'crash': 'Cash out in time • no limit',
    'hilo': 'High or low • × grows each win', 'mines': 'Safe cells • cash out anytime',
    'keno': 'Pick 10/40 • 3 hits pay, 10 = 20000×',
}
UNLOCK = {'coin': 1, 'dice': 1, 'slot': 1, 'hilo': 1, 'roulette': 2, 'race': 2, 'plinko': 2, 'tombala': 3,
          'wheel': 3, 'crash': 3, 'blackjack': 4, 'scratch': 4, 'mines': 4, 'keno': 4, 'baccarat': 5,
          'poker': 6}                                # level needed per game
CATEGORIES = [('BEGINNER GAMES', ['coin', 'dice', 'slot', 'hilo']),
              ('ADVANCED GAMES', ['roulette', 'blackjack', 'poker']),
              ('CHANCE GAMES', ['tombala', 'wheel', 'scratch', 'keno']),
              ('BETTING GAMES', ['race', 'baccarat']),
              ('ARCADE GAMES', ['plinko', 'crash', 'mines'])]
LOBBY_ORDER = [k for _, keys in CATEGORIES for k in keys]      # keyboard shortcuts follow this order
GAME_HOTKEYS = dict(zip(LOBBY_ORDER, ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0',
                                     'Alt+1', 'Alt+2', 'Alt+3', 'Alt+4', 'Alt+5', 'Alt+6']))

# ---------------------------------------------------------------- progression
CLEAN_TARGET = 10                  # days without gambling for the willpower reward
CLEAN_STREAKS_FOR_ENDING = 3       # completed clean streaks for the "Reformed" ending
REFORMED_MIN_GAMES = 30            # ...and you must have gambled at least this much before
BANK_INTEREST = 0.01               # per day
BANK_INTEREST_CAP_PER_LEVEL = 25   # max interest paid per day = 25 TL x level
EVENT_CHANCE = 0.30                # chance of a random event when a day passes

# ---------------------------------------------------------------- loan shark (Tefeci / black money)
# A second, much nastier credit line: no credit check, but 6% a day, a hard deadline and a visit
# from the collector. The upside is that his channels clean 15% extra out of your wins while you owe.
SHARK_LIMIT_PER_LEVEL = 2000       # his ceiling at level 1, +2000 per level
SHARK_RATE = 0.06                  # interest per day (compounding)
SHARK_DAYS = 4                      # days until the collector knocks on the door
SHARK_COLLECT_SHARE = 0.25          # the collector seizes this share of your wallet (up to the debt)
SHARK_COLLECT_MENTAL = -15          # mental health cost of that visit
SHARK_CLEAN = 0.15                  # bonus added to wins while you owe him (money laundering)
SHARK_SPIRAL_MULT = 3               # shark_debt >= 3x his ceiling = the "Debt Spiral" ending
LEVEL_EXP = [0, 20, 60, 120, 200, 320, 480, 700, 1000, 1400]          # exp needed for level 1..10
MAX_BET = [50, 100, 250, 500, 1000, 2500, 5000, 10000, 25000, 10 ** 9]  # max bet per level

JOBS = [
    {'key': 'courier', 'name': 'Delivery Courier', 'level': 1, 'pay': 75, 'exp': 5, 'bonus': 50, 'stress': 10},
    {'key': 'cashier', 'name': 'Cashier', 'level': 2, 'pay': 110, 'exp': 7, 'bonus': 80, 'stress': 10},
    {'key': 'clerk', 'name': 'Office Clerk', 'level': 4, 'pay': 180, 'exp': 10, 'bonus': 130, 'stress': 12},
    {'key': 'accountant', 'name': 'Accountant', 'level': 6, 'pay': 300, 'exp': 15, 'bonus': 220, 'stress': 15},
    {'key': 'manager', 'name': 'Manager', 'level': 8, 'pay': 500, 'exp': 22, 'bonus': 350, 'stress': 18},
]
JOB_BY_KEY = {j['key']: j for j in JOBS}

# ---------------------------------------------------------------- difficulty
# `edge` is the house edge of the edge-based games (Crash, Mines, Hi-Lo): the player gets
# 100% - edge back on average. Easy is generous, Hard bleeds you.
EDGE_GAMES = ('crash', 'mines', 'hilo')
DIFFICULTIES = {
    'easy': {'name': 'Easy', 'start': 250, 'mental_loss': 3, 'debt_rate': 0.02, 'goal': 30_000,
             'credit_per_level': 300, 'pay_mult': 1.2, 'shop_mult': 0.8, 'edge': 0.05,
             'desc': 'Start with 250 TL. Losing costs 3 mental health, loans are cheap, work pays 20% more, '
                     'the shop is 20% cheaper and Crash, Mines & Hi-Lo pay back 95%. Goal: 30,000 TL.'},
    'normal': {'name': 'Normal', 'start': 100, 'mental_loss': 5, 'debt_rate': 0.03, 'goal': 50_000,
               'credit_per_level': 250, 'pay_mult': 1.0, 'shop_mult': 1.0, 'edge': 0.08,
               'desc': 'Start with 100 TL. Losing costs 5 mental health, loans cost 3% a day and Crash, '
                       'Mines & Hi-Lo pay back 92%. Goal: 50,000 TL.'},
    'hard': {'name': 'Hard', 'start': 50, 'mental_loss': 8, 'debt_rate': 0.04, 'goal': 100_000,
             'credit_per_level': 150, 'pay_mult': 0.85, 'shop_mult': 1.25, 'edge': 0.12,
             'desc': 'Start with 50 TL. Losing costs 8 mental health, loans cost 4% a day and are small, '
                     'work pays 15% less, the shop is 25% pricier and Crash, Mines & Hi-Lo pay back only '
                     '88%. Goal: 100,000 TL.'},
}

# ---------------------------------------------------------------- streak side bet (B6)
# Payouts for "win N games in a row". The odds are priced off STREAK_P_MAX, the highest win
# probability any eligible game can reach (Slot: 0.52), so the side bet can never be farmed by
# grinding a near-certain game: EV <= 0.92 x stake - stake for every strategy.
STREAK_P_MAX = 0.52
STREAK_BETS = {3: 6.5, 5: 24, 7: 89, 10: 630}          # target -> total multiplier (stake included)
STREAK_GAMES = ['coin', 'dice', 'roulette', 'blackjack', 'slot', 'tombala', 'poker', 'baccarat', 'race',
                'wheel', 'scratch', 'plinko', 'keno']   # cash-out games cannot be part of a streak bet

# ---------------------------------------------------------------- career tenure (C3)
# (days worked in one run, title) - layered on top of the 7-day work streak
TENURE_RANKS = [(0, 'New Hire'), (5, 'Rookie'), (15, 'Trusted Hand'), (30, 'Floor Veteran'),
                (50, 'Department Chief'), (80, 'Company Legend')]


def tenure_rank(days):
    """The index of the highest rank already reached."""
    idx = 0
    for i, (need, _title) in enumerate(TENURE_RANKS):
        if days >= need:
            idx = i
    return idx

# ---------------------------------------------------------------- shop
# kind: service = used immediately, consumable = kept until it triggers, permanent = bought once
ITEMS = [
    {'key': 'therapy', 'name': 'Therapy Session', 'kind': 'service', 'price': 100, 'level': 1, 'scales': True,
     'desc': 'Restores 25 mental health. Once every 2 days.'},
    {'key': 'energy', 'name': 'Energy Drink', 'kind': 'service', 'price': 60, 'level': 1, 'scales': True,
     'desc': 'Removes your work cooldown.'},
    {'key': 'charm', 'name': 'Lucky Charm', 'kind': 'consumable', 'price': 200, 'level': 2,
     'desc': 'Your next win pays 25% extra.'},
    {'key': 'insurance', 'name': 'Loss Insurance', 'kind': 'consumable', 'price': 150, 'level': 3,
     'desc': 'Your next loss refunds half the bet and costs no mental health.'},
    {'key': 'course', 'name': 'Night Classes', 'kind': 'permanent', 'price': 1000, 'level': 2,
     'desc': '+25% experience from everything.'},
    {'key': 'pet', 'name': 'Pet Cat', 'kind': 'permanent', 'price': 500, 'level': 2,
     'desc': '+2 mental health every new day.'},
    {'key': 'apartment', 'name': 'Comfy Apartment', 'kind': 'permanent', 'price': 1500, 'level': 3,
     'desc': 'Resting (a day without games) restores 15 mental health instead of 10.'},
    {'key': 'car', 'name': 'Used Car', 'kind': 'permanent', 'price': 2500, 'level': 4,
     'desc': '+20% pay at work.'},
    {'key': 'advisor', 'name': 'Financial Advisor', 'kind': 'permanent', 'price': 3000, 'level': 5,
     'desc': 'Bank interest cap doubled and loan interest 1 point lower.'},
    {'key': 'vip', 'name': 'VIP Card', 'kind': 'permanent', 'price': 5000, 'level': 6,
     'desc': 'Maximum bet doubled.'},
    {'key': 'second_wind', 'name': 'Second Wind', 'kind': 'consumable', 'price': 150, 'level': 3,
     'desc': 'Your next loss costs no mental health and heals 10 instead. No money is refunded.'},
    {'key': 'streak_book', 'name': 'Streak Notebook', 'kind': 'permanent', 'price': 800, 'level': 4,
     'desc': 'Shows the live odds of a streak bet and lets you cash it out at its fair value '
             'after any win.'},
]
ITEM_BY_KEY = {i['key']: i for i in ITEMS}
PERMANENT_ITEMS = [i['key'] for i in ITEMS if i['kind'] == 'permanent']
THERAPY_COOLDOWN_DAYS = 2

# ---------------------------------------------------------------- achievements and endings
# key, title, description, exp reward
ACHIEVEMENTS = [
    ('first_win', 'First Blood', 'Win your first game.', 5),
    ('games_50', 'Regular', 'Play 50 games in one run.', 15),
    ('games_200', 'Addict?', 'Play 200 games in one run.', 40),
    ('win_5', 'Hot Streak', 'Win 5 games in a row.', 15),
    ('lose_5', 'Cold Streak', 'Lose 5 games in a row.', 10),
    ('allin_win', 'Fortune Favors the Bold', 'Win a game betting your whole wallet.', 25),
    ('big_win', 'Big Fish', 'Win 1,000 TL or more in a single game.', 30),
    ('jackpot', 'Jackpot!', 'Hit a jackpot (slot, lotto, crash, plinko, mines or hi-lo).', 40),
    ('natural', 'Natural', 'Win with a blackjack from your first two cards.', 15),
    ('lotto_4', 'Lucky Numbers', 'Match 4 or more numbers in Lotto.', 15),
    ('all_games', 'Tried Everything', 'Play every game at least once in one run.', 30),
    ('rich_1k', 'Comfortable', 'Reach 1,000 TL net worth.', 15),
    ('rich_10k', 'Wealthy', 'Reach 10,000 TL net worth.', 40),
    ('saver', 'Saver', 'Have 500 TL in the bank.', 10),
    ('borrower', 'In The Red', 'Take out your first loan.', 5),
    ('shark_free', 'Off His List', 'Pay the loan shark back in full.', 25),
    ('debt_free', 'Debt Free', 'Fully repay your debt.', 20),
    ('workaholic', 'Workaholic', 'Complete a 7-day work streak.', 20),
    ('promoted', 'Climbing The Ladder', 'Get a job as Manager.', 50),
    ('level_5', 'Seasoned', 'Reach level 5.', 0),
    ('level_10', 'Legend', 'Reach level 10.', 0),
    ('clean_10', 'Clean Streak', 'Stay away from gambling for 10 days.', 20),
    ('rest_bottom', 'Hanging On', 'Survive with 10 or less mental health.', 15),
    ('events_5', 'Eventful', 'Make 5 decisions in random events.', 15),
    ('shopper', 'Treat Yourself', 'Buy something in the shop.', 5),
    ('collector', 'Fully Equipped', 'Own every permanent shop item.', 60),
    ('hard_win', 'Hard Mode, Hard Won', 'Reach the money goal on Hard difficulty.', 100),
    ('crash_5x', 'To The Moon', 'Cash out a Crash round at 5× or more.', 25),
    ('plinko_edge', 'Edge Case', 'Land Plinko in a corner slot.', 25),
    ('mines_clear', 'Demolition Expert', 'Clear the entire Mines board without touching a mine.', 40),
    ('hilo_7', 'Card Sharp', 'Win seven Hi-Lo guesses in a row.', 40),
    ('big_5k', 'Whale', 'Win 5,000 TL or more in a single game.', 50),
    ('clean_30', 'Cold Turkey', 'Stay away from gambling for 30 days in a row.', 40),
    ('streak_bet', 'Sure Thing?', 'Win a streak side bet.', 30),
]
ACH_BY_KEY = {k: (t, d, r) for k, t, d, r in ACHIEVEMENTS}

ENDINGS = {
    'high_roller': ('High Roller', 'good',
                    'You reached {goal} TL and walked away with your head on straight. The tables will '
                    'remember your name, but you no longer need them.'),
    'hollow': ('Hollow Victory', 'neutral',
               'You hit the money goal, but your mind was long gone. You can afford anything except feeling '
               'okay. Maybe the real jackpot was the sleep you lost along the way.'),
    'reformed': ('Reformed', 'good',
                 'Three times you stayed away from the tables for ten days straight. Somewhere along the way '
                 'you stopped chasing the next bet. Life got quieter, and better.'),
    'breakdown': ('Breakdown', 'bad',
                  'Your mental health hit zero. The lights, the noise, the losses... it all became too much. '
                  'Time to start over, and maybe do things differently.'),
    'bankrupt': ('Bankrupt', 'bad',
                 'No money, no credit, nothing left to bet. The bank closed its doors to you, and so did '
                 'the casino.'),
    'debt_spiral': ('Debt Spiral', 'bad',
                    'The interest grew faster than you could pay it. The calls never stopped, and in the end '
                    'everything was taken.'),
}


def level_for(exp):
    return sum(1 for t in LEVEL_EXP if exp >= t)
