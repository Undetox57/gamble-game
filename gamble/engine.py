"""All of the game's economy and life logic, with no Qt in it.

The window drives this for the player and simulate.py drives it with bots, so both play by the same rules.
Messages go through `log_fn(msg, kind)`; kind is info / win / loss / warn.
"""
import math
import random

from .config import (ACH_BY_KEY, BANK_INTEREST, CLEAN_STREAKS_FOR_ENDING, CLEAN_TARGET, DIFFICULTIES,
                     ENDINGS, EVENT_CHANCE, GAME_NAMES, ITEM_BY_KEY, JOB_BY_KEY, JOBS, LEVEL_EXP, MAX_BET,
                     PERMANENT_ITEMS, REFORMED_MIN_GAMES, STREAK_BETS, STREAK_GAMES, STREAK_P_MAX,
                     TENURE_RANKS, THERAPY_COOLDOWN_DAYS, UNLOCK, tenure_rank)
from .events import build_events
from .state import BET_HISTORY_LIMIT, HISTORY_LIMIT, GameState, MetaState

TAG_ACHIEVEMENTS = {'jackpot': 'jackpot', 'natural': 'natural', 'lotto4': 'lotto_4', 'crash_5x': 'crash_5x',
                    'edge': 'plinko_edge', 'board_clear': 'mines_clear', 'hilo_7': 'hilo_7'}


class Engine:
    def __init__(self, state=None, meta=None, rng=None, persist=True):
        self.state = state or GameState()
        self.meta = meta or MetaState()
        self.rng = rng or random.Random()
        self.persist = persist          # False = never touch the save files (simulator)
        self.events = build_events()
        self.pending_events = []
        self.log_fn = None
        self.celebrate_fn = None

    # ---- plumbing
    def log(self, msg, kind='info'):
        if self.log_fn:
            self.log_fn(msg, kind)

    def celebrate(self):
        if self.celebrate_fn:
            self.celebrate_fn()

    def save(self):
        if self.meta.record(self.state.difficulty, self.state.net_worth) and self.persist:
            self.meta.save()                        # a new best for this difficulty is worth keeping
        if self.persist:
            err = self.state.save()
            if err:
                self.log(f'[ERROR] {err}', 'loss')

    def save_meta(self):
        if self.persist:
            self.meta.save()

    # ---- small helpers
    def add_mental(self, n):
        s = self.state
        s.mental = max(0, min(100, s.mental + n))

    def change(self, money=0, mental=0, exp=0, bank=0, debt=0):
        """Apply a bundle of changes and return a short summary for the log."""
        s = self.state
        parts = []
        if money:
            s.balance += money
            parts.append(f'{money:+,} TL')
        if bank:
            s.bank += bank
            parts.append(f'{bank:+,} TL in bank')
        if debt:
            s.debt = max(0, s.debt + debt)
            parts.append(f'{debt:+,} TL debt')
        if mental:
            self.add_mental(mental)
            parts.append(f'{mental:+} mental health')
        if exp:
            self.gain_exp(exp)
            parts.append(f'{exp:+} exp')
        return '(' + ', '.join(parts) + ')' if parts else ''

    def pay(self, amount):
        """Pay from the wallet; whatever is missing is added to the debt. Returns the part that became debt."""
        s = self.state
        from_wallet = min(amount, max(0, s.balance))
        s.balance -= from_wallet
        rest = amount - from_wallet
        s.debt += rest
        return rest

    # ---- experience, levels, achievements
    def gain_exp(self, n):
        s = self.state
        if s.has('course'):
            n = math.floor(n * 1.25 + self.rng.random())      # +25%, rounded without bias
        old = s.level
        s.exp += n
        for lv in range(old + 1, s.level + 1):
            bonus = 25 * lv
            s.balance += bonus
            self.add_mental(10)
            maxbet = 'no limit' if MAX_BET[lv - 1] >= 10 ** 9 else f'{MAX_BET[lv - 1] * (2 if s.has("vip") else 1):,} TL'
            msg = (f'LEVEL UP! You are now level {lv}. Bonus: +{bonus} TL and +10 mental health. '
                   f'Max bet: {maxbet}. Credit limit: {s.diff["credit_per_level"] * lv:,} TL.')
            games = [GAME_NAMES[k] for k, level in UNLOCK.items() if level == lv]
            jobs = [j['name'] for j in JOBS if j['level'] == lv]
            shop = [i['name'] for i in ITEM_BY_KEY.values() if i['level'] == lv and lv > 1]
            if games:
                msg += ' Unlocked: ' + ', '.join(games) + '.'
            if jobs:
                msg += ' New job: ' + ', '.join(jobs) + '.'
            if shop:
                msg += ' New in the shop: ' + ', '.join(shop) + '.'
            self.log(msg, 'win')
            self.celebrate()

    def award(self, key):
        if key in self.meta.achievements:
            return
        title, _desc, reward = ACH_BY_KEY[key]
        self.meta.achievements.add(key)
        self.save_meta()
        self.log(f'ACHIEVEMENT UNLOCKED: {title}' + (f' (+{reward} exp)' if reward else ''), 'warn')
        if reward:
            self.gain_exp(reward)

    def check_achievements(self):
        s = self.state
        played = s.total_played
        conds = {
            'first_win': any(v['won'] for v in s.stats.values()),
            'games_50': played >= 50, 'games_200': played >= 200,
            'win_5': s.win_streak >= 5, 'lose_5': s.loss_streak >= 5,
            'all_games': all(v['played'] for v in s.stats.values()),
            'rich_1k': s.net_worth >= 1000, 'rich_10k': s.net_worth >= 10000,
            'saver': s.bank >= 500, 'workaholic': s.streaks_done >= 1, 'promoted': s.job == 'manager',
            'level_5': s.level >= 5, 'level_10': s.level >= 10, 'clean_10': s.clean_streaks >= 1,
            'rest_bottom': 0 < s.mental <= 10, 'events_5': s.events_seen >= 5,
            'collector': all(s.has(k) for k in PERMANENT_ITEMS),
            'big_5k': s.best_win >= 5000, 'clean_30': s.no_gamble_days >= 30,
        }
        for k, ok in conds.items():
            if ok:
                self.award(k)

    # ---- time
    def advance_day(self, dec_cooldown=True):
        s = self.state
        s.day += 1
        s.games_today = 0
        if s.out_days > 0:
            s.out_days -= 1
        if dec_cooldown and s.work_cooldown > 0:
            s.work_cooldown -= 1
        self.log(f'Day has passed! Now it is day {s.day}.', 'warn')
        if s.has('pet'):
            self.add_mental(2)
        if s.bank > 0:
            cap = s.bank_interest_cap
            earned = round(min(s.bank * BANK_INTEREST, cap), 2)
            if earned >= 0.01:
                s.bank += earned
                self.log(f'Your bank paid {earned:,.2f} TL interest ({BANK_INTEREST * 100:.0f}% per day, '
                         f'max {cap:,} TL).', 'win')
        if s.debt > 0:
            interest = max(1, round(s.debt * s.debt_rate))
            s.debt += interest
            self.log(f'Your debt grew by {interest:,} TL ({s.debt_rate * 100:.0f}% daily interest).', 'loss')
            if s.debt > s.credit_limit:
                self.add_mental(-3)
                self.log('You are over your credit limit. The calls keep coming (-3 mental health).', 'loss')
        s.history.append((s.day, s.net_worth))
        if len(s.history) > HISTORY_LIMIT:
            s.history = s.history[::2][:-1] + [s.history[-1]]      # thin out old points, keep the newest
        if self.rng.random() < EVENT_CHANCE:
            options = [e for e in self.events if e['cond'](s)]
            if options:
                self.pending_events.append(self.rng.choice(options))

    def check_clean_reward(self):
        s = self.state
        if s.no_gamble_days >= CLEAN_TARGET:
            s.no_gamble_days = 0
            s.clean_streaks += 1
            s.balance += 150
            self.add_mental(25)
            self.gain_exp(30)
            self.log(f'{CLEAN_TARGET} days without gambling! Willpower reward: +150 TL, +25 mental health, '
                     f'+30 exp. (Clean streak {s.clean_streaks}/{CLEAN_STREAKS_FOR_ENDING})', 'win')

    # ---- playing games
    def apply_item_modifiers(self, delta, win, bet):
        """Lucky Charm / Loss Insurance. Returns (new delta, insured, notes)."""
        s, notes, insured = self.state, [], False
        if win is True and delta > 0 and s.items.get('charm', 0) > 0:
            bonus = max(1, int(delta * 0.25))
            delta += bonus
            s.items['charm'] -= 1
            notes.append(f'Lucky Charm: +{bonus} TL')
        elif win is False and s.items.get('insurance', 0) > 0:
            refund = min(bet // 2, -delta)
            delta += refund
            s.items['insurance'] -= 1
            insured = True
            notes.append(f'Loss Insurance refunded {refund} TL')
        return delta, insured, notes

    def finish_game(self, key, delta, win, bet, tags=(), insured=False):
        """Everything that follows a finished round (same rules as the console version, plus exp,
        achievements and profit tracking). `delta` already includes item bonuses."""
        s = self.state
        all_in = bet >= s.balance
        s.balance += delta
        st = s.stats[key]
        st['played'] += 1
        s.profit[key] = s.profit.get(key, 0) + delta
        s.best_win = max(s.best_win, delta)
        s.worst_loss = min(s.worst_loss, delta)
        s.bet_history.append((key, delta))                   # the last rounds shown in Statistics
        if len(s.bet_history) > BET_HISTORY_LIMIT:
            del s.bet_history[:-BET_HISTORY_LIMIT]
        self.streak_side(key, win)                           # the running streak side bet, if any
        lost_game = False
        if win is True:
            st['won'] += 1
            s.win_streak += 1
            s.loss_streak = 0
        elif win is False:
            st['lost'] += 1
            lost_game = True
            s.loss_streak += 1
            s.win_streak = 0
        if lost_game and insured:
            self.log('Your insurance protected your mental health.', 'info')
        elif lost_game and s.items.get('second_wind', 0) > 0:
            s.items['second_wind'] -= 1
            self.add_mental(10)
            self.log('Second Wind: the loss cost you no mental health - you bounced back (+10).', 'win')
        elif lost_game and s.out_days == 0:
            loss = s.diff['mental_loss']
            s.mental = max(0, s.mental - loss)
            self.log(f'Losing affected your mental health (-{loss}).', 'loss')
        elif lost_game and s.out_days > 0:
            self.log('You lost, but spending time with your loved one protected your mental health.', 'info')
        if 0 < s.work_streak < 7:
            self.log('You played a game before completing 7 work days. Your boss got angry and reset your work '
                     'streak!', 'loss')
            s.work_streak = 0
        s.games_today += 1
        if s.games_today >= 5:
            self.advance_day()
        self.gain_exp(2 if win is True else 1)
        if win is True and all_in:
            self.award('allin_win')
        if delta >= 1000:
            self.award('big_win')
        for tag in tags:
            if tag in TAG_ACHIEVEMENTS:
                self.award(TAG_ACHIEVEMENTS[tag])
        if (win is True and delta >= 4 * bet) or 'jackpot' in tags:
            self.celebrate()
        self.save()

    def settle(self, key, delta, win, bet, tags=()):
        """Item modifiers + aftermath in one call (what the simulator uses). Returns the final delta."""
        delta, insured, _notes = self.apply_item_modifiers(delta, win, bet)
        self.finish_game(key, delta, win, bet, tags, insured)
        return delta

    # ---- streak side bet (B6)
    def place_streak(self, target, stake):
        """Buy a "win N games in a row" side bet. The stake leaves the wallet immediately, so a
        player can never be up money by abandoning a run. Returns False when it is not allowed."""
        s = self.state
        if target not in STREAK_BETS or s.sb_stake:
            return False
        stake = int(stake)
        if stake < 1 or stake > s.balance:
            return False
        s.balance -= stake
        s.sb_stake, s.sb_target, s.sb_count = stake, target, 0
        self.log(f'Streak bet placed: win {target} games in a row for {STREAK_BETS[target]:g}x '
                 f'({stake:,} TL at stake).', 'info')
        self.save()
        return True

    def streak_side(self, key, win):
        """Advance or break the running streak side bet. Called once per finished round:
        cash-out games (Crash / Mines / Hi-Lo) and pushes leave the bet untouched, only the
        one-shot games can build or break it."""
        s = self.state
        if s.sb_count < 0 or not s.sb_stake:
            return
        if key not in STREAK_GAMES or win is None:
            return
        if win is False:
            stake = s.sb_stake
            s.sb_stake = s.sb_target = s.sb_count = 0
            self.log(f'Streak bet lost ({stake:,} TL gone) - a game in the run did not win.', 'loss')
            return
        s.sb_count += 1
        if s.sb_count >= s.sb_target:
            payout = int(s.sb_stake * STREAK_BETS[s.sb_target])
            s.balance += payout
            self.log(f'STREAK BET WON! {s.sb_target} in a row pays {STREAK_BETS[s.sb_target]:g}x '
                     f'= {payout:,} TL.', 'win')
            self.award('streak_bet')
            self.celebrate()
            s.sb_stake = s.sb_target = s.sb_count = 0
        else:
            self.log(f'Streak bet: {s.sb_count}/{s.sb_target} - keep winning.', 'info')

    def streak_cash_value(self):
        """What a running streak bet is worth right now (its fair, probability-weighted value).
        Only the Streak Notebook lets you take it; taking it changes no expected value, it only
        turns a gamble into a certainty."""
        s = self.state
        if not s.sb_stake or not s.sb_count:
            return 0
        left = max(0, s.sb_target - s.sb_count)
        return int(s.sb_stake * STREAK_BETS[s.sb_target] * (STREAK_P_MAX ** left))

    def cash_out_streak(self):
        """The Streak Notebook's perk: bank the current fair value of a running streak bet."""
        s = self.state
        if not s.has('streak_book'):
            self.log('Cashing a streak bet out early needs the Streak Notebook from the shop.', 'warn')
            return False
        value = self.streak_cash_value()
        if value <= 0:
            return False
        s.balance += value
        s.sb_stake = s.sb_target = s.sb_count = 0
        self.log(f'Streak bet cashed out: {value:,} TL banked. The rest of the run is yours to play.',
                 'win')
        self.save()
        return True

    # ---- life actions
    def work_factor(self):
        s = self.state
        return s.diff['pay_mult'] * (1.2 if s.has('car') else 1.0)

    def work_pay(self):
        return round(self.state.job_info['pay'] * self.work_factor() * self.tenure_factor())

    def work_bonus(self):
        return round(self.state.job_info['bonus'] * self.work_factor())

    def tenure_factor(self):
        """Seniority pays: +5% per tenure rank (New Hire -> Company Legend, see config.TENURE_RANKS)."""
        return 1 + 0.05 * tenure_rank(self.state.worked_days)

    def tenure_title(self):
        return TENURE_RANKS[tenure_rank(self.state.worked_days)][1]

    def pass_day(self):
        s = self.state
        if s.games_today == 0:
            rest = 15 if s.has('apartment') else 10
            s.skipped_days += 1
            self.add_mental(rest)
            self.log(f'You rested and regained some mental health (+{rest}).', 'win')
            s.no_gamble_days += 1
            self.check_clean_reward()
        else:
            s.no_gamble_days = 0
        self.advance_day()
        self.save()

    def go_work(self):
        s = self.state
        job = s.job_info
        if s.work_cooldown > 0:
            self.log(f'You are too tired to work. You can go to work in {s.work_cooldown} day(s).', 'warn')
            return False
        old_rank = tenure_rank(s.worked_days)
        s.worked_days += 1                          # career tenure: every shift counts
        pay, bonus = self.work_pay(), self.work_bonus()
        if tenure_rank(s.worked_days) != old_rank:
            self.log(f'TENURE PROMOTION: you are now a {self.tenure_title()} - every shift pays 5% more.',
                     'warn')
        s.work_streak += 1
        s.balance += pay
        self.gain_exp(job['exp'])
        self.advance_day(dec_cooldown=False)
        if s.work_streak >= 7:
            s.balance += bonus
            s.work_cooldown = 3
            self.add_mental(-job['stress'])
            s.streaks_done += 1
            self.log(f'Congratulations! You went to work for 7 consecutive days and earned {bonus + pay} TL!', 'win')
            s.work_streak = 0
        else:
            self.log(f'You went to work as {job["name"]} ({self.tenure_title()})! You earned {pay} TL and '
                     f'gained {job["exp"]} experience.', 'win')
        s.no_gamble_days += 1
        self.check_clean_reward()
        self.save()
        return True

    def take_job(self, key):
        s = self.state
        job = JOB_BY_KEY[key]
        if s.level < job['level'] or s.job == key:
            return False
        s.job = key
        if s.work_streak:
            s.work_streak = 0
            self.log(f'You are now a {job["name"]}. Your work streak was reset.', 'warn')
        else:
            self.log(f'You are now a {job["name"]}.', 'warn')
        self.save()
        return True

    def go_out(self):
        s = self.state
        if s.balance < 100:
            self.log('You do not have enough money to go out with your loved one! (Need 100 TL)', 'warn')
            return False
        s.balance -= 100
        s.out_days = 7
        self.log('You went out with your loved one! For the next 7 days, you will not lose mental health '
                 'from losing.', 'win')
        self.save()
        return True

    # ---- bank and loans
    def deposit(self, amt):
        s = self.state
        if amt <= 0 or amt > s.balance:
            self.log('Invalid amount!', 'warn')
            return False
        s.balance -= amt
        s.bank += amt
        self.log(f'Deposited! Bank balance is now: {s.bank:,.2f} TL', 'info')
        self.save()
        return True

    def withdraw(self, amt):
        s = self.state
        if amt <= 0 or amt > s.bank:
            self.log('Invalid amount!', 'warn')
            return False
        s.bank -= amt
        s.balance += amt
        self.log(f'Withdrawn! Bank balance is now: {s.bank:,.2f} TL', 'info')
        self.save()
        return True

    def borrow(self, amt):
        s = self.state
        if amt <= 0 or amt > s.credit_available:
            self.log('You cannot borrow that much.', 'warn')
            return False
        s.balance += amt
        s.debt += amt
        self.log(f'Borrowed {amt:,} TL. Your debt is now {s.debt:,} TL ({s.debt_rate * 100:.0f}% interest per day).',
                 'warn')
        self.award('borrower')
        self.save()
        return True

    def repay(self, amt):
        s = self.state
        if amt <= 0 or amt > s.balance or amt > s.debt:
            self.log('Invalid amount!', 'warn')
            return False
        s.balance -= amt
        s.debt -= amt
        self.log(f'Repaid {amt:,} TL. Your debt is now {s.debt:,} TL.', 'win')
        if s.debt == 0:
            self.award('debt_free')
        self.save()
        return True

    # ---- shop
    def price(self, key):
        s, item = self.state, ITEM_BY_KEY[key]
        p = item['price'] * s.diff['shop_mult']
        if item.get('scales'):
            p *= 1 + 0.2 * (s.level - 1)
        return max(1, int(round(p)))

    def item_status(self, key):
        """(can buy, short reason if not)."""
        s, item = self.state, ITEM_BY_KEY[key]
        if s.level < item['level']:
            return False, f'Requires level {item["level"]}'
        if item['kind'] == 'permanent' and s.has(key):
            return False, 'Owned'
        if key == 'therapy':
            left = THERAPY_COOLDOWN_DAYS - (s.day - s.last_therapy_day)
            if left > 0:
                return False, f'Again in {left} day(s)'
        if key == 'energy' and s.work_cooldown == 0:
            return False, 'You are not tired'
        if s.balance < self.price(key):
            return False, 'Not enough money'
        return True, ''

    def buy(self, key):
        ok, reason = self.item_status(key)
        if not ok:
            self.log(f'You cannot buy that: {reason}.', 'warn')
            return False
        s, item = self.state, ITEM_BY_KEY[key]
        s.balance -= self.price(key)
        if key == 'therapy':
            self.add_mental(25)
            s.last_therapy_day = s.day
            self.log('The therapy session helped a lot (+25 mental health).', 'win')
        elif key == 'energy':
            s.work_cooldown = 0
            self.log('You feel ready to work again.', 'win')
        else:
            s.items[key] = s.items.get(key, 0) + 1
            self.log(f'You bought: {item["name"]}. {item["desc"]}', 'win')
        self.award('shopper')
        self.save()
        return True

    # ---- random events
    def run_event(self, ev, idx):
        msg, kind = ev['choices'][idx][2](self)
        self.state.events_seen += 1
        self.log(f'[{ev["title"]}] {msg}', kind)
        self.save()

    def first_enabled_choice(self, ev):
        for i, (_label, enabled, _fn) in enumerate(ev['choices']):
            if enabled is None or enabled(self.state):
                return i
        return len(ev['choices']) - 1

    # ---- endings
    def check_endings(self):
        """Returns an ending key (and records it) or None."""
        s = self.state
        key = None
        if s.mental <= 0:
            key = 'breakdown'
        elif s.debt > 0 and s.debt >= 3 * s.credit_limit:
            key = 'debt_spiral'
        elif s.balance <= 0 and s.bank <= 0 and s.credit_available < 1:
            key = 'bankrupt'
        elif s.net_worth >= s.goal and not s.won_goal:
            s.won_goal = 1
            key = 'high_roller' if s.mental >= 50 else 'hollow'
            if s.difficulty == 'hard':
                self.award('hard_win')
        elif (s.clean_streaks >= CLEAN_STREAKS_FOR_ENDING and s.total_played >= REFORMED_MIN_GAMES
              and not s.reformed):
            s.reformed = 1
            key = 'reformed'
        if key:
            self.meta.endings.add(key)
            self.save_meta()
            self.log(f'ENDING: {ENDINGS[key][0]}', 'warn')
        return key

    def new_game(self, difficulty):
        self.pending_events.clear()
        self.state.reset(difficulty)
        self.log(f'Starting a new game on {DIFFICULTIES[self.state.difficulty]["name"]} difficulty... '
                 '(achievements and endings are kept)', 'warn')
        self.save()

    def end_run(self, start_over, difficulty=None):
        if start_over:
            self.new_game(difficulty or self.state.difficulty)
        else:
            self.save()

    # ---- level info for the UI
    def level_progress(self):
        """(exp into this level, exp needed for the level, is max level)."""
        s = self.state
        lv = s.level
        lo = LEVEL_EXP[lv - 1]
        if lv >= len(LEVEL_EXP):
            return s.exp - lo, 1, True
        return s.exp - lo, LEVEL_EXP[lv] - lo, False
