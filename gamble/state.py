"""Game state and its save files. Still reads/writes the console version's savegame.txt format:
the first lines are identical, everything new goes into "x:key:value" lines the old game ignores."""
import os

from . import config
from .config import (ACH_BY_KEY, BANK_INTEREST_CAP_PER_LEVEL, DIFFICULTIES, ENDINGS, GAME_KEYS, JOB_BY_KEY,
                     MAX_BET, level_for)

HISTORY_LIMIT = 400
BET_HISTORY_LIMIT = 60                 # how many recent bets are kept in the save (20 are shown)


def new_stats():
    return {k: {'played': 0, 'won': 0, 'lost': 0} for k in GAME_KEYS}


class GameState:
    EXTRA_INT = ['debt', 'won_goal', 'reformed', 'clean_streaks', 'loss_streak', 'win_streak', 'events_seen',
                 'streaks_done', 'best_win', 'worst_loss', 'last_therapy_day',
                 'sb_stake', 'sb_target', 'sb_count',   # the streak side bet (0 = none)
                 'worked_days',                         # career tenure (C3): days worked in this run
                 'shark_debt', 'shark_due']             # loan shark: owed TL and the day he comes to collect

    def __init__(self):
        self.set_defaults()

    def set_defaults(self):
        self.balance = 100
        self.bank = 0.0
        self.stats = new_stats()
        self.day = 1
        self.skipped_days = 0
        self.work_streak = 0
        self.mental = 100
        self.out_days = 0
        self.exp = 0
        self.work_cooldown = 0
        self.no_gamble_days = 0
        self.games_today = 0
        self.job = 'courier'
        self.difficulty = 'normal'
        self.items = {}                              # item key -> count (permanent items: 1)
        self.profit = {k: 0 for k in GAME_KEYS}      # net winnings per game in this run
        self.history = [(1, 100)]                    # (day, net worth) for the chart
        self.bet_history = []                        # [(game key, delta), newest last] - last rounds only
        for k in self.EXTRA_INT:
            setattr(self, k, 0)
        self.last_therapy_day = -99

    # ---- derived values
    @property
    def diff(self):
        return DIFFICULTIES[self.difficulty]

    @property
    def goal(self):
        return self.diff['goal']

    @property
    def level(self):
        return level_for(self.exp)

    def has(self, key):
        return self.items.get(key, 0) > 0

    @property
    def max_bet(self):
        return MAX_BET[self.level - 1] * (2 if self.has('vip') else 1)

    @property
    def credit_limit(self):
        return self.diff['credit_per_level'] * self.level

    @property
    def credit_available(self):
        return max(0, self.credit_limit - self.debt)

    @property
    def debt_rate(self):
        return max(0.0, self.diff['debt_rate'] - (0.01 if self.has('advisor') else 0.0))

    @property
    def bank_interest_cap(self):
        return BANK_INTEREST_CAP_PER_LEVEL * self.level * (2 if self.has('advisor') else 1)

    @property
    def net_worth(self):
        return int(self.balance + self.bank - self.debt - self.shark_debt)

    @property
    def shark_limit(self):
        """The most the loan shark will ever advance you, at your current level."""
        return config.SHARK_LIMIT_PER_LEVEL * self.level

    @property
    def job_info(self):
        return JOB_BY_KEY[self.job]

    @property
    def total_played(self):
        return sum(v['played'] for v in self.stats.values())

    # ---- new run
    def start_run(self, difficulty):
        self.difficulty = difficulty if difficulty in DIFFICULTIES else 'normal'
        self.balance = self.diff['start']
        self.history = [(1, self.balance)]

    def reset(self, difficulty='normal'):
        if os.path.exists(config.SAVE_FILE):
            try:
                os.remove(config.SAVE_FILE)
            except Exception:
                pass
        self.set_defaults()
        self.start_run(difficulty)

    # ---- files
    def load(self):
        """Returns an error string or None."""
        if not os.path.exists(config.SAVE_FILE):
            return None
        try:
            with open(config.SAVE_FILE, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            if not lines:
                return None

            def geti(i, default):
                return int(lines[i].strip()) if len(lines) > i else default

            balance = int(float(lines[0].strip()))
            bank = float(lines[1].strip()) if len(lines) > 1 else 0.0
            vals = (geti(2, 1), geti(3, 0), geti(4, 0), geti(5, 100), geti(6, 0), geti(7, 0), geti(8, 0), geti(9, 0))
            stats = new_stats()
            extras, items, profit = {}, {}, {k: 0 for k in GAME_KEYS}
            history, bets = [], []
            for line in lines[10:]:
                p = line.strip().split(':')
                if len(p) == 4 and p[0] in stats:
                    stats[p[0]] = {'played': int(p[1]), 'won': int(p[2]), 'lost': int(p[3])}
                elif len(p) == 3 and p[0] == 'x':
                    key, val = p[1], p[2]
                    if key.startswith('i_'):
                        items[key[2:]] = int(val)
                    elif key.startswith('p_') and key[2:] in profit:
                        profit[key[2:]] = int(float(val))
                    elif key == 'hist':
                        history = [(int(d), int(v)) for d, v in (x.split('=') for x in val.split(',') if x)]
                    elif key == 'bets':
                        for one in val.split(','):         # the last rounds: "coin=10,dice=-5"
                            name, sep, delta = one.partition('=')
                            if sep and name in GAME_KEYS:
                                bets.append((name, int(delta)))
                        bets = bets[-BET_HISTORY_LIMIT:]
                    else:
                        extras[key] = val
            extra_ints = {k: int(float(extras.get(k, -99 if k == 'last_therapy_day' else 0)))
                          for k in self.EXTRA_INT}
            job = extras.get('job', 'courier')
            difficulty = extras.get('difficulty', 'normal')
            self.balance, self.bank, self.stats = balance, bank, stats
            (self.day, self.skipped_days, self.work_streak, self.mental,
             self.out_days, self.exp, self.work_cooldown, self.no_gamble_days) = vals
            self.job = job if job in JOB_BY_KEY else 'courier'
            self.difficulty = difficulty if difficulty in DIFFICULTIES else 'normal'
            self.items = {k: v for k, v in items.items() if v > 0 and k in config.ITEM_BY_KEY}
            self.profit = profit
            for k, v in extra_ints.items():
                setattr(self, k, v)
            self.history = history or [(self.day, self.net_worth)]
            self.bet_history = bets
            return None
        except Exception as e:
            self.set_defaults()
            return f'Could not load game: {e}'

    def save(self):
        try:
            with open(config.SAVE_FILE, 'w', encoding='utf-8') as f:
                f.write(f'{self.balance}\n{self.bank}\n{self.day}\n{self.skipped_days}\n{self.work_streak}\n'
                        f'{self.mental}\n{self.out_days}\n{self.exp}\n{self.work_cooldown}\n{self.no_gamble_days}\n')
                for key in self.stats:
                    s = self.stats[key]
                    f.write(f"{key}:{s['played']}:{s['won']}:{s['lost']}\n")
                f.write(f'x:job:{self.job}\nx:difficulty:{self.difficulty}\n')
                for k in self.EXTRA_INT:
                    f.write(f'x:{k}:{getattr(self, k)}\n')
                for k, n in self.items.items():
                    if n > 0:
                        f.write(f'x:i_{k}:{n}\n')
                for k, v in self.profit.items():
                    f.write(f'x:p_{k}:{v}\n')
                if self.bet_history:
                    f.write('x:bets:' + ','.join(f'{k}={d}' for k, d in self.bet_history[-BET_HISTORY_LIMIT:])
                            + '\n')
                f.write('x:hist:' + ','.join(f'{d}={v}' for d, v in self.history[-HISTORY_LIMIT:]) + '\n')
            return None
        except Exception as e:
            return f'Could not save game: {e}'


class MetaState:
    """Achievements, endings and per-difficulty records survive resets, so they live in their own file."""

    def __init__(self):
        self.achievements = set()
        self.endings = set()
        self.records = {k: 0 for k in DIFFICULTIES}   # best net worth ever reached on each difficulty

    def record(self, difficulty, net_worth):
        """Remember the best net worth of a difficulty. Returns True when it is a new best."""
        if difficulty not in self.records:
            return False
        value = int(net_worth)
        if value <= self.records[difficulty]:
            return False
        self.records[difficulty] = value
        return True

    def load(self):
        try:
            if os.path.exists(config.META_FILE):
                with open(config.META_FILE, 'r', encoding='utf-8') as f:
                    for line in f:
                        kind, _, key = line.strip().partition(':')
                        if kind == 'ach' and key in ACH_BY_KEY:
                            self.achievements.add(key)
                        elif kind == 'end' and key in ENDINGS:
                            self.endings.add(key)
                        elif kind == 'rec':                  # rec:<difficulty>:<best net worth>
                            diff, _, val = key.partition(':')
                            if diff in DIFFICULTIES:
                                try:
                                    self.records[diff] = max(self.records[diff], int(float(val)))
                                except ValueError:
                                    pass
        except Exception:
            pass

    def save(self):
        try:
            with open(config.META_FILE, 'w', encoding='utf-8') as f:
                for k in sorted(self.achievements):
                    f.write(f'ach:{k}\n')
                for k in sorted(self.endings):
                    f.write(f'end:{k}\n')
                for k in sorted(self.records):
                    if self.records[k]:
                        f.write(f'rec:{k}:{self.records[k]}\n')
        except Exception:
            pass
