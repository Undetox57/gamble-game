"""Tests for the rules and the engine. No Qt needed:   python -m unittest discover -s tests"""
import math
import os
import random
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gamble import config, rules                       # noqa: E402
from gamble.engine import Engine, TAG_ACHIEVEMENTS     # noqa: E402
from gamble.state import GameState, MetaState          # noqa: E402
import simulate                                        # noqa: E402


class RulesTest(unittest.TestCase):
    def test_exact_returns_are_house_favoured(self):
        exact = {'slot': rules.slot_rtp(), 'wheel': rules.wheel_rtp(), 'scratch': rules.scratch_rtp(),
                 'lotto': rules.lotto_rtp(), 'keno': rules.keno_rtp(), 'crash': rules.crash_rtp(),
                 'mines': rules.mines_rtp(), 'hi-lo': rules.hilo_rtp(),
                 **{f'plinko {r}': rules.plinko_rtp(r) for r in rules.PLINKO_TABLES}}
        for name, rtp in exact.items():
            self.assertTrue(0.85 < rtp < 0.95, f'{name}: {rtp:.4f}')

    def test_keno_payout_table_is_exactly_priced(self):
        """Keno is a hypergeometric draw, so its RTP can be computed - and must match a simulation."""
        probs = [rules.keno_hit_prob(h) for h in range(rules.KENO_PICK + 1)]
        self.assertAlmostEqual(sum(probs), 1.0, places=9, msg='the hit probabilities must cover every draw')
        self.assertAlmostEqual(rules.keno_rtp(), 0.9005, places=4, msg='the table is priced at ~90%')
        self.assertEqual(rules.settle_keno(3, 100)[0], 0, '3 hits is a push, not a win')
        self.assertEqual(rules.settle_keno(4, 100)[0], 50, '4 hits pays 1.5x total')
        self.assertEqual(rules.settle_keno(5, 100)[0], 300, '5 hits pays 4x total')
        self.assertEqual(rules.settle_keno(0, 100)[0], -100)
        self.assertEqual(rules.settle_keno(10, 100)[3], ('jackpot',))
        for hits in range(rules.KENO_PICK + 1):
            delta, win, text, _tags = rules.settle_keno(hits, 100)
            self.assertIn(win, (True, False, None), hits)
            self.assertEqual(win is True, delta > 0, hits)
            self.assertTrue(text)
        rng = random.Random(7)
        rets = [(100 + simulate.r_keno(rng, 100)[0]) / 100 for _ in range(40000)]
        mean = sum(rets) / len(rets)
        err = (sum((r - mean) ** 2 for r in rets) / len(rets)) ** 0.5 / math.sqrt(len(rets))
        self.assertLess(abs(mean - rules.keno_rtp()), 4 * err + 0.01, 'measured Keno RTP drifts from its price')

    def test_every_game_key_is_wired_up(self):
        """A new game must be listed everywhere the code iterates over the games."""
        from gamble import style
        self.assertEqual(sorted(config.LOBBY_ORDER), sorted(config.GAME_KEYS), 'CATEGORIES lost a game')
        self.assertEqual(len(config.GAME_HOTKEYS), len(config.GAME_KEYS), 'not every game has a shortcut')
        self.assertEqual(len(set(config.GAME_HOTKEYS.values())), len(config.GAME_KEYS), 'shortcut collision')
        for key in config.GAME_KEYS:
            self.assertIn(key, config.GAME_NAMES, key)
            self.assertIn(key, config.GAME_SUBTITLES, key)
            self.assertIn(key, config.UNLOCK, key)
            self.assertIn(key, style.GAME_ICONS, key)
            self.assertGreater(rules.game_rtp(key), 0.5, f'{key} pays nothing')
        # every game is either part of a streak bet or a cash-out game (the three edge games)
        self.assertEqual(set(config.GAME_KEYS) - set(config.STREAK_GAMES), set(config.EDGE_GAMES))
        self.assertIn('keno', config.LOBBY_ORDER)
        self.assertIn('keno', config.STREAK_GAMES)

    def test_simulated_returns_match_and_nothing_prints_money(self):
        rng = random.Random(5)
        for name, (_key, play) in simulate.ROUNDS.items():
            rets = [(100 + play(rng, 100)[0]) / 100 for _ in range(30000)]
            mean = sum(rets) / len(rets)
            err = (sum((r - mean) ** 2 for r in rets) / len(rets)) ** 0.5 / math.sqrt(len(rets))
            if name == 'coin':                                  # the one deliberately fair game
                self.assertLess(abs(mean - 1), 4 * err, name)
            else:
                self.assertLess(mean + 3 * err, 1.0, f'{name} has no house edge: {mean:.3f}')

    def test_crash_survival_curve(self):
        rng = random.Random(9)
        pts = [rules.crash_point(rng) for _ in range(100000)]
        self.assertAlmostEqual(sum(p <= 1.0 for p in pts) / len(pts), rules.CRASH_EDGE, delta=0.01)
        for x in (2, 5):
            self.assertAlmostEqual(sum(p >= x for p in pts) / len(pts), (1 - rules.CRASH_EDGE) / x, delta=0.01)

    def test_scratch_grids(self):
        rng = random.Random(3)
        for _ in range(3000):
            mult = rules.scratch_roll(rng)
            win_sym, cells = rules.scratch_grid(mult, rng)
            triples = [c for c in set(cells) if cells.count(c) >= 3]
            self.assertEqual(triples, [win_sym] if mult else [])

    def test_settle_functions_are_consistent(self):
        for bet in (1, 5, 10, 100):
            for out in (rules.settle_coin('h', 'h', bet), rules.settle_slot(list('AAB'), bet),
                        rules.settle_wheel(3, bet), rules.settle_lotto(2, bet),
                        rules.settle_plinko([True] * 8, 'high', bet), rules.settle_crash(2.0, 3.0, bet),
                        rules.settle_poker((1, []), (1, []), bet), rules.settle_baccarat('player', 5, 5, bet),
                        rules.settle_mines(2.5, bet), rules.settle_mines(0, bet, boom=True),
                        rules.settle_hilo(2.5, bet), rules.settle_hilo(None, bet, 'You guessed higher')):
                delta, win, text, tags = out
                self.assertIn(win, (True, False, None))
                self.assertEqual(win is True, delta > 0, out)
                self.assertTrue(text)

    def test_mines_multiplier_keeps_92_percent(self):
        """Every pick count - so every stopping strategy - must return the same 92%."""
        cells = rules.MINES_CELLS
        for mines in rules.MINES_RISK.values():
            for k in range(1, cells - mines + 1):
                survive = 1.0
                for i in range(k):
                    survive *= (cells - mines - i) / (cells - i)
                ret = rules.mines_multiplier(k, mines) * survive
                self.assertAlmostEqual(ret, 0.92, delta=0.01, msg=f'{mines} mines, {k} picks: {ret:.4f}')
        rng = random.Random(6)
        for mines in rules.MINES_RISK.values():
            for _ in range(40):
                layout = rules.mines_layout(mines, rng)
                self.assertEqual(len(layout), mines)
                self.assertTrue(all(0 <= i < cells for i in layout), layout)

    def test_hilo_multiplier_keeps_92_percent(self):
        """Every streak length - so every stopping strategy - must return the same 92%."""
        for probs in ([0.5], [0.9], [0.5, 0.75], [0.9, 0.3, 0.6], [1.0, 0.5], [0.7] * 8):
            p = 1.0
            for w in probs:
                p *= w
            ret = rules.hilo_multiplier(probs) * p
            self.assertAlmostEqual(ret, 0.92, delta=0.01, msg=f'{probs}: {ret:.4f}')
        self.assertEqual(rules.hilo_multiplier([0.99]), 1.0,
                         'a near-certain guess may not pay out less than the stake')

    def test_hilo_odds_split_the_deck_and_never_deal_a_tie(self):
        rng = random.Random(4)
        deck = rules.new_deck_hilo(rng)
        while len(deck) > 6:
            current = deck.pop()
            up = rules.hilo_prob(deck, current[0], True)
            down = rules.hilo_prob(deck, current[0], False)
            self.assertAlmostEqual(up + down, 1.0, places=9)
            nxt = rules.hilo_draw(deck, current[0])
            if nxt is None:
                break
            self.assertNotEqual(nxt[0], current[0], 'ties must be re-dealt')
        # a fresh deck holds 51 cards for the first guess; only the three same ranks can be thrown away
        deck = rules.new_deck_hilo(rng)
        first = deck.pop()
        drawn = 0
        while True:
            nxt = rules.hilo_draw(deck, first[0])
            if nxt is None:
                break
            drawn += 1
        self.assertEqual(drawn, 48)


class EngineTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.old = (config.SAVE_FILE, config.META_FILE, config.SETTINGS_FILE)
        config.SAVE_FILE = os.path.join(self.tmp.name, 'savegame.txt')
        config.META_FILE = os.path.join(self.tmp.name, 'meta.txt')
        config.SETTINGS_FILE = os.path.join(self.tmp.name, 'settings.txt')
        self.e = Engine(rng=random.Random(1), persist=False)
        self.s = self.e.state
        self.msgs = []
        self.e.log_fn = lambda m, k='info': self.msgs.append(m)

    def tearDown(self):
        config.SAVE_FILE, config.META_FILE, config.SETTINGS_FILE = self.old
        self.tmp.cleanup()

    def test_difficulty(self):
        for d, start, loss in (('easy', 250, 3), ('normal', 100, 5), ('hard', 50, 8)):
            self.s.set_defaults()
            self.s.start_run(d)
            self.s.exp = 100
            self.s.mental = 100
            self.assertEqual(self.s.balance, start)
            self.e.settle('coin', -10, False, 10) if self.s.balance >= 10 else self.e.finish_game('coin', -10, False, 10)
            self.assertEqual(self.s.mental, 100 - loss)

    def test_shop_items(self):
        s, e = self.s, self.e
        s.exp, s.balance = 1400, 100000
        pay = e.work_pay()
        self.assertTrue(e.buy('car'))
        self.assertEqual(e.work_pay(), round(pay * 1.2))
        self.assertFalse(e.buy('car'), 'permanent items are bought once')
        e.buy('vip')
        self.assertGreaterEqual(s.max_bet, config.MAX_BET[9])
        s.mental = 40
        e.buy('therapy')
        self.assertEqual(s.mental, 65)
        self.assertFalse(e.item_status('therapy')[0], 'therapy has a cooldown')
        e.buy('charm')
        d, _ins, notes = e.apply_item_modifiers(100, True, 100)
        self.assertEqual(d, 125)
        self.assertTrue(notes and not s.items.get('charm'))
        e.buy('insurance')
        d, ins, _n = e.apply_item_modifiers(-100, False, 100)
        self.assertEqual((d, ins), (-50, True))
        s.balance = 10
        self.assertFalse(e.buy('apartment'), 'cannot afford it')

    def test_clean_days_reward(self):
        s, e = self.s, self.e
        s.no_gamble_days = 9
        e.pass_day()
        self.assertEqual((s.clean_streaks, s.no_gamble_days), (1, 0))

    def test_loans_and_interest(self):
        s, e = self.s, self.e
        e.borrow(200)
        self.assertEqual((s.debt, s.balance), (200, 300))
        e.advance_day()
        self.assertEqual(s.debt, 206)                     # 3% on normal
        self.assertTrue(e.repay(206))
        self.assertIn('debt_free', e.meta.achievements)

    def test_loan_shark_lends_collects_and_is_paid_off(self):
        s, e = self.s, self.e
        self.assertEqual(s.shark_limit, config.SHARK_LIMIT_PER_LEVEL)      # level 1
        self.assertEqual((s.shark_debt, s.shark_due), (0, 0))
        self.assertTrue(e.shark_borrow(1500))
        self.assertEqual(s.shark_debt, 1500)
        self.assertEqual(s.shark_due, s.day + config.SHARK_DAYS, 'every advance buys SHARK_DAYS of time')
        self.assertFalse(e.shark_borrow(600), 'he never lends past his ceiling')
        self.assertFalse(e.shark_borrow(0))
        e.advance_day()                                                   # one day of 6% interest
        self.assertEqual(s.shark_debt, 1500 + max(1, round(1500 * config.SHARK_RATE)))
        while s.day < s.shark_due - 1:                                    # walk up to the day before
            e.advance_day()
        owed, bal, mood = s.shark_debt, s.balance, s.mental
        self.assertEqual((owed, s.day), (1786, s.shark_due - 1), 'interest compounds every single day')
        e.advance_day()                                                   # the deadline: he knocks
        interest = max(1, round(owed * config.SHARK_RATE))
        seized = min(int(bal * config.SHARK_COLLECT_SHARE), owed + interest)
        self.assertEqual(s.shark_debt, owed + interest - seized)
        self.assertEqual(s.balance, bal - seized, 'he takes a quarter of the wallet, capped by the debt')
        self.assertEqual(s.mental, mood + config.SHARK_COLLECT_MENTAL)
        self.assertGreater(s.shark_debt, 0, 'he does not forgive the rest')
        self.assertEqual(s.shark_due, s.day + config.SHARK_DAYS, '...but he gives you more time')
        # pay him off in full (max level first: the achievement's 25 exp would level you up otherwise)
        s.exp, s.balance, s.mental = config.LEVEL_EXP[-1], 100_000, 50
        self.assertFalse(e.shark_pay(10 ** 6), 'cannot pay more than you owe')
        self.assertTrue(e.shark_pay(s.shark_debt))
        self.assertEqual((s.shark_debt, s.shark_due), (0, 0))
        self.assertEqual(s.mental, 60, 'being free of him lifts a weight')
        self.assertIn('shark_free', e.meta.achievements)

    def test_shark_cleans_your_winnings_but_not_your_losses(self):
        s, e = self.s, self.e
        d, _ins, notes = e.apply_item_modifiers(100, True, 100)
        self.assertEqual(d, 100, 'no debt, no laundering bonus')
        s.shark_debt = 500
        d, _ins, notes = e.apply_item_modifiers(100, True, 100)
        self.assertEqual(d, 115, '15% extra while you owe him')
        self.assertTrue(any('shark' in n.lower() for n in notes), notes)
        d, _ins, _n = e.apply_item_modifiers(-100, False, 100)
        self.assertEqual(d, -100, 'a loss is never cleaned')
        s.shark_debt = 0

    def test_shark_debt_is_net_worth_and_can_end_the_run(self):
        s, e = self.s, self.e
        s.balance, s.bank, s.debt = 1000, 500, 0
        self.assertEqual(s.net_worth, 1500)
        s.shark_debt = 400
        self.assertEqual(s.net_worth, 1100, 'money you owe the shark is not yours')
        s.set_defaults()
        s.start_run('normal')
        s.shark_debt = config.SHARK_SPIRAL_MULT * s.shark_limit + 1
        self.assertEqual(e.check_endings(), 'debt_spiral')
        s.set_defaults()
        s.start_run('normal')
        self.assertIsNone(e.check_endings())

    def test_shark_state_is_saved_and_old_saves_load(self):
        s = self.s
        s.shark_debt, s.shark_due = 750, 9
        self.assertIsNone(s.save())
        t = GameState()
        self.assertIsNone(t.load())
        self.assertEqual((t.shark_debt, t.shark_due), (750, 9))
        with open(config.SAVE_FILE, encoding='utf-8') as f:                # a save from before the shark
            lines = [ln for ln in f if not ln.startswith('x:shark_')]
        with open(config.SAVE_FILE, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        u = GameState()
        self.assertIsNone(u.load())
        self.assertEqual((u.shark_debt, u.shark_due), (0, 0), 'old saves simply owe him nothing')
        self.assertEqual(u.net_worth, u.balance + int(u.bank) - u.debt)

    def test_tournament_holds_the_entry_and_scores_the_window(self):
        s, e = self.s, self.e
        s.exp = config.LEVEL_EXP[-1]                                  # max level: no level-up side effects
        s.balance = 100
        self.assertFalse(e.enter_tournament(), 'the entry fee has to be covered')
        self.assertEqual(s.tour_active, 0)
        s.balance = 5000
        self.assertTrue(e.enter_tournament())
        self.assertEqual(s.balance, 5000 - config.TOURNAMENT_ENTRY)
        self.assertEqual((s.tour_active, s.tour_day, s.tour_net), (1, s.day, 4000),
                         'the score starts from the net worth AFTER the fee was held')
        self.assertFalse(e.enter_tournament(), 'only one tournament at a time')
        s.balance -= 3000                                            # you finish the window behind
        for _ in range(config.TOURNAMENT_DAYS):
            e.advance_day()
        self.assertEqual(s.tour_active, 0, 'the window closes after TOURNAMENT_DAYS days')
        self.assertEqual(s.balance, 5000 - config.TOURNAMENT_ENTRY - 3000, 'going backwards forfeits the fee')
        self.assertEqual(e.meta.tournaments[s.difficulty], 0, 'a negative result is not a record')
        self.assertIn('tour_finish', e.meta.achievements)
        self.assertNotIn('tour_record', e.meta.achievements)
        # second attempt: finish in the black and the entry comes back with a bonus
        s.balance = 5000
        self.assertTrue(e.enter_tournament())
        start_day = s.day
        s.balance += 2000
        for _ in range(config.TOURNAMENT_DAYS):
            e.advance_day()
        self.assertEqual(s.day, start_day + config.TOURNAMENT_DAYS)
        bonus = min(config.TOURNAMENT_BONUS_CAP, int(2000 * config.TOURNAMENT_BONUS_RATE))
        self.assertEqual(s.balance, 5000 - config.TOURNAMENT_ENTRY + 2000 + config.TOURNAMENT_ENTRY + bonus)
        self.assertEqual(e.meta.tournaments[s.difficulty], 2000, 'the best result is kept per difficulty')
        self.assertIn('tour_record', e.meta.achievements)
        self.assertEqual(e.meta.tournaments['hard'], 0, 'records stay separate per difficulty')

    def test_tournament_state_is_saved_and_old_saves_load(self):
        s = self.s
        s.tour_active, s.tour_day, s.tour_net = 1, 7, -300
        self.assertIsNone(s.save())
        t = GameState()
        self.assertIsNone(t.load())
        self.assertEqual((t.tour_active, t.tour_day, t.tour_net), (1, 7, -300))
        with open(config.SAVE_FILE, encoding='utf-8') as f:            # a save from before the tournament
            lines = [ln for ln in f if not ln.startswith('x:tour_')]
        with open(config.SAVE_FILE, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        u = GameState()
        self.assertIsNone(u.load())
        self.assertEqual((u.tour_active, u.tour_day, u.tour_net), (0, 0, 0))
        # tournament records live in the meta file, next to achievements and net worth records
        meta = MetaState()
        self.assertTrue(meta.record_tournament('normal', 1200))
        self.assertFalse(meta.record_tournament('normal', 500), 'only a better result replaces it')
        self.assertIsNone(meta.save())
        m2 = MetaState()
        m2.load()
        self.assertEqual(m2.tournaments['normal'], 1200)
        self.assertEqual(m2.tournaments['hard'], 0)
        with open(config.META_FILE, encoding='utf-8') as f:            # an old meta file has no tou: lines
            text = ''.join(ln for ln in f if not ln.startswith('tou:'))
        with open(config.META_FILE, 'w', encoding='utf-8') as f:
            f.write(text)
        m3 = MetaState()
        m3.load()
        self.assertEqual(m3.tournaments['normal'], 0, 'old meta files simply have no tournament yet')
        self.assertEqual(m2.achievements, m3.achievements, 'achievements must survive untouched')

    def test_endings(self):
        s, e = self.s, self.e
        s.mental = 0
        self.assertEqual(e.check_endings(), 'breakdown')
        s.set_defaults(); s.start_run('normal'); s.balance = 0; s.debt = 250
        self.assertEqual(e.check_endings(), 'bankrupt')
        s.set_defaults(); s.start_run('normal'); s.debt = 800
        self.assertEqual(e.check_endings(), 'debt_spiral')
        s.set_defaults(); s.start_run('normal'); s.balance = 60000
        self.assertEqual(e.check_endings(), 'high_roller')
        self.assertIsNone(e.check_endings(), 'a goal ending is shown only once')
        s.set_defaults(); s.start_run('hard'); s.balance = 120000; s.mental = 20
        self.assertEqual(e.check_endings(), 'hollow')
        self.assertIn('hard_win', e.meta.achievements)
        s.set_defaults(); s.start_run('normal'); s.clean_streaks = 3
        self.assertIsNone(e.check_endings(), 'Reformed needs some gambling first')
        s.stats['coin']['played'] = config.REFORMED_MIN_GAMES
        self.assertEqual(e.check_endings(), 'reformed')

    def test_history_is_recorded_and_thinned(self):
        s, e = self.s, self.e
        for _ in range(900):
            e.advance_day()
        self.assertLessEqual(len(s.history), 400)
        self.assertEqual(s.history[-1][0], s.day)

    def test_streak_side_bet(self):
        s, e = self.s, self.e
        s.balance = 1000
        e.meta.achievements.add('streak_bet')               # already earned: no level-up money in the way
        self.assertTrue(e.place_streak(3, 10))
        self.assertEqual(s.balance, 990, 'the stake leaves the wallet on placement')
        self.assertFalse(e.place_streak(5, 10), 'only one streak bet may run at a time')
        self.assertFalse(e.place_streak(99, 10), 'unknown targets are refused')
        e.streak_side('crash', False)                     # cash-out games cannot break it
        e.streak_side('mines', True)                      # nor advance it
        e.streak_side('coin', None)                       # a push is neutral
        self.assertEqual(s.sb_count, 0)
        e.streak_side('coin', True)
        e.streak_side('dice', True)
        self.assertEqual(s.sb_count, 2)
        before = s.balance
        e.streak_side('slot', True)                       # the third win pays out
        self.assertEqual((s.sb_stake, s.sb_target, s.sb_count), (0, 0, 0))
        self.assertEqual(s.balance, before + int(10 * config.STREAK_BETS[3]))
        self.assertTrue(e.place_streak(3, 10))            # and a new one can be placed right away
        e.streak_side('coin', True)
        e.streak_side('coin', False)                      # a loss drops the whole bet
        self.assertEqual((s.sb_stake, s.sb_count), (0, 0))
        s.balance = 5
        self.assertFalse(e.place_streak(3, 10), 'you cannot stake more than you own')

    def test_streak_bet_is_wired_into_a_finished_round(self):
        s, e = self.s, self.e
        s.balance = 1000
        self.assertTrue(e.place_streak(5, 20))
        e.finish_game('coin', 20, True, 20)
        self.assertEqual(s.sb_count, 1, 'a won round must advance the streak bet')
        e.finish_game('crash', -20, False, 20)
        self.assertEqual(s.sb_count, 1, 'Crash must not touch the streak bet')

    def test_bet_history_is_recorded_and_saved(self):
        from gamble.state import BET_HISTORY_LIMIT
        s, e = self.s, self.e
        e.finish_game('coin', 10, True, 10)
        e.finish_game('dice', -5, False, 5)
        self.assertEqual(s.bet_history, [('coin', 10), ('dice', -5)])
        for i in range(BET_HISTORY_LIMIT + 40):
            e.finish_game('slot', -1, False, 1)
        self.assertEqual(len(s.bet_history), BET_HISTORY_LIMIT)
        self.assertIsNone(s.save())
        t = GameState()
        self.assertIsNone(t.load())
        self.assertEqual(t.bet_history, s.bet_history)

    # ------------------------------------------------------------------ C group
    def test_tenure_ranks_raise_the_pay(self):
        s, e = self.s, self.e
        self.assertEqual((s.worked_days, e.tenure_title()), (0, config.TENURE_RANKS[0][1]))
        base = e.work_pay()
        for _ in range(55):
            s.work_cooldown, s.work_streak, s.no_gamble_days = 0, 0, 0
            self.assertTrue(e.go_work())
        self.assertEqual(s.worked_days, 55)
        self.assertGreater(e.work_pay(), base, 'seniority must pay more than day one')
        self.assertEqual(e.tenure_title(), config.TENURE_RANKS[config.tenure_rank(55)][1])
        self.assertEqual(config.tenure_rank(0), 0)
        self.assertEqual(config.tenure_rank(10 ** 6), len(config.TENURE_RANKS) - 1)
        self.assertIsNone(s.save())
        t = GameState()
        self.assertIsNone(t.load())
        self.assertEqual(t.worked_days, 55, 'the tenure must be in the save file')

    def test_second_wind_saves_the_mind_but_not_the_money(self):
        s, e = self.s, self.e
        s.mental, s.items['second_wind'] = 40, 1
        before = s.balance
        e.finish_game('coin', -10, False, 10)
        self.assertEqual(s.mental, 50, 'Second Wind turns a loss into +10 mental health')
        self.assertEqual(s.items.get('second_wind', 0), 0, 'the item is used up')
        self.assertEqual(s.balance, before - 10, 'it never gives money back')
        e.finish_game('coin', -10, False, 10)
        self.assertEqual(s.mental, 50 - s.diff['mental_loss'], 'the next loss is normal again')

    def test_streak_notebook_cashes_out_at_fair_value(self):
        s, e = self.s, self.e
        s.balance = 1000
        e.meta.achievements.add('streak_bet')
        self.assertFalse(e.cash_out_streak(), 'without the notebook there is no cash-out')
        s.items['streak_book'] = 1
        self.assertTrue(e.place_streak(3, 100))
        self.assertEqual(e.streak_cash_value(), 0, 'before the first win there is nothing to bank')
        self.assertFalse(e.cash_out_streak())
        e.streak_side('coin', True)
        want = int(100 * config.STREAK_BETS[3] * config.STREAK_P_MAX ** 2)
        self.assertEqual(e.streak_cash_value(), want)
        before = s.balance
        self.assertTrue(e.cash_out_streak())
        self.assertEqual(s.balance, before + want)
        self.assertEqual((s.sb_stake, s.sb_count), (0, 0))
        self.assertTrue(e.place_streak(3, 10), 'the notebook does not lock the bet forever')

    def test_new_achievements_are_wired_up(self):
        s, e = self.s, self.e
        for key in ('mines_clear', 'hilo_7', 'big_5k', 'clean_30', 'streak_bet'):
            self.assertIn(key, config.ACH_BY_KEY, key)
        self.assertEqual(TAG_ACHIEVEMENTS.get('board_clear'), 'mines_clear')
        self.assertEqual(TAG_ACHIEVEMENTS.get('hilo_7'), 'hilo_7')
        e.finish_game('mines', 20, True, 10, tags=('board_clear',))
        self.assertIn('mines_clear', e.meta.achievements)
        e.finish_game('hilo', 20, True, 10, tags=('hilo_7',))
        self.assertIn('hilo_7', e.meta.achievements)
        s.best_win, s.no_gamble_days = 5000, 30
        e.check_achievements()
        self.assertIn('big_5k', e.meta.achievements)
        self.assertIn('clean_30', e.meta.achievements)

    def test_per_difficulty_records_survive_the_meta_file(self):
        s, e = self.s, self.e
        self.assertTrue(e.meta.record('normal', 500))
        self.assertFalse(e.meta.record('normal', 400), 'records only ever go up')
        self.assertFalse(e.meta.record('unknown', 999))
        e.meta.record('hard', 900)
        self.assertIsNone(e.meta.save())
        m = MetaState()
        m.load()
        self.assertEqual((m.records['normal'], m.records['hard']), (500, 900))
        with open(config.META_FILE, 'a', encoding='utf-8') as f:        # what an old meta file looks like
            f.write('ach:first_win\nend:high_roller\n')
        m2 = MetaState()
        m2.load()
        self.assertIn('first_win', m2.achievements)
        s.balance = 5000
        e.save()
        self.assertEqual(e.meta.records['normal'], 5000, 'the engine records its own run')

    def test_difficulty_edge_reaches_the_simulator(self):
        easy, hard = simulate.exact_rtp(0.05), simulate.exact_rtp(0.12)
        self.assertAlmostEqual(easy['mines (3 picks)'], 0.95, places=6)
        self.assertAlmostEqual(hard['hi-lo (3 guesses)'], 0.88, places=6)
        self.assertGreater(easy['crash @2x'], hard['crash @2x'], 'a kinder difficulty pays more')
        self.assertEqual(easy['slot'], hard['slot'], 'fixed-payout games never change with difficulty')
        rng = random.Random(3)
        rounds = simulate.build_rounds(0.05)
        rets = [(100 + rounds['mines (3 picks)'][1](rng, 100)[0]) / 100 for _ in range(10000)]
        self.assertGreater(sum(rets) / len(rets), 0.90, 'Easy Mines must pay about 95%')

    def test_save_roundtrip_and_old_saves(self):
        s = self.s
        s.start_run('hard')
        s.items = {'car': 1, 'charm': 2}
        s.profit['slot'] = -77
        s.best_win, s.worst_loss = 300, -90
        s.history = [(1, 50), (2, 80)]
        self.assertIsNone(s.save())
        t = GameState()
        self.assertIsNone(t.load())
        self.assertEqual((t.difficulty, t.items, t.profit['slot'], t.best_win, t.worst_loss, t.history),
                         ('hard', {'car': 1, 'charm': 2}, -77, 300, -90, [(1, 50), (2, 80)]))
        with open(config.SAVE_FILE, 'w') as f:                  # a save from the console version
            f.write('250\n10.5\n12\n3\n2\n80\n0\n40\n0\n4\ncoin:5:3:2\ndice:1:0:1\n')
        t = GameState()
        self.assertIsNone(t.load())
        self.assertEqual((t.balance, t.difficulty, t.items, t.stats['coin']['won']), (250, 'normal', {}, 3))

    def test_a_save_from_before_keno_still_loads(self):
        """A save written before the 16th game existed must load with empty Keno counters."""
        with open(config.SAVE_FILE, 'w') as f:              # the old console format
            f.write('250\n10.5\n12\n3\n2\n80\n0\n40\n0\n4\ncoin:5:3:2\n')
        t = GameState()
        self.assertIsNone(t.load())
        self.assertEqual(t.stats['keno'], {'played': 0, 'won': 0, 'lost': 0})
        self.assertEqual(t.profit['keno'], 0)
        t.stats['keno'] = {'played': 1, 'won': 1, 'lost': 0}
        t.profit['keno'] = 40
        self.assertIsNone(t.save())
        with open(config.SAVE_FILE, encoding='utf-8') as f:
            text = f.read()
        self.assertIn('keno:1:1:0', text)
        self.assertIn('x:p_keno:40', text)

    def test_reset_never_deletes_other_files(self):
        meta = MetaState()
        meta.achievements.add('first_win')
        meta.save()
        self.s.save()
        self.s.reset('easy')
        self.assertFalse(os.path.exists(config.SAVE_FILE))
        self.assertTrue(os.path.exists(config.META_FILE))

    def test_simulator_is_deterministic_and_leaves_saves_alone(self):
        self.s.save()
        a = simulate.one_run('normal', 'cautious', 11, 200)
        b = simulate.one_run('normal', 'cautious', 11, 200)
        self.assertEqual(a, b)
        self.assertTrue(os.path.exists(config.SAVE_FILE), 'the simulator must not delete savegame.txt')


if __name__ == '__main__':
    unittest.main()
