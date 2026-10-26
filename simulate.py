#!/usr/bin/env python3
"""Balance simulator for the Gamble Game. No GUI needed, and it never touches your save files.

It plays with the game's real rules (gamble/rules.py) and real economy (gamble/engine.py), so what it
measures is what you get in the game.

  python simulate.py rtp                      return-to-player of every game with a simple bot strategy
  python simulate.py run                      full runs with 4 kinds of bots on every difficulty
  python simulate.py run --difficulty hard --bots gambler,worker --runs 500 --days 800

Reading the 'run' table: each bot plays whole games until an ending (or until --days pass).
If almost every worker reaches the goal in 80 days the goal is too easy; if nobody ever does it is too hard.
"""
import argparse
import math
import random
import statistics
from collections import Counter

from gamble import config, rules
from gamble.engine import Engine
from gamble.state import GameState, MetaState


# =============================================================== one round of every game, with a bot strategy
def r_coin(rng, bet):
    return rules.settle_coin('h', rules.coin_flip(rng), bet)


def r_dice(rng, bet):
    return rules.settle_dice(rng.randint(1, 6), rng.randint(1, 6), bet)


def r_roulette(rng, bet):
    return rules.settle_roulette('black', None, rng.choice(rules.roulette_table(rng)), bet)


def r_roulette_number(rng, bet):
    table = rules.roulette_table(rng)
    black = [n for n, c in table if c == 'black']
    return rules.settle_roulette('black', rng.choice(black), rng.choice(table), bet)


def r_blackjack(rng, bet, hit_below=17):
    deck = rules.new_deck_bj(rng)
    player, dealer = [deck.pop(), deck.pop()], [deck.pop(), deck.pop()]
    while rules.bj_value(player) < hit_below:
        player.append(deck.pop())
    if rules.bj_value(player) > 21:
        return rules.settle_bust(bet)
    while rules.bj_value(dealer) < 17:
        dealer.append(deck.pop())
    return rules.settle_blackjack(player, dealer, bet)


def r_slot(rng, bet):
    return rules.settle_slot(rules.slot_spin(rng), bet)


def r_lotto(rng, bet):
    chosen = set(rng.sample(range(1, rules.LOTTO_POOL + 1), 6))
    return rules.settle_lotto(len(chosen & set(rules.lotto_draw(rng))), bet)


def r_poker(rng, bet):
    deck = rules.new_deck_poker(rng)
    hand, computer = [deck.pop() for _ in range(5)], [deck.pop() for _ in range(5)]
    keep = rules.keep_indices(hand)
    for i in range(5):
        if i not in keep:
            hand[i] = deck.pop()
    rules.computer_draw(computer, deck, rng)
    return rules.settle_poker(rules.poker_hand_rank(hand), rules.poker_hand_rank(computer), bet)


def r_baccarat(rng, bet):
    deck = rules.new_deck_bac(rng)
    p, b = [deck.pop(), deck.pop()], [deck.pop(), deck.pop()]
    return rules.settle_baccarat('player', rules.bac_total(p), rules.bac_total(b), bet)


def r_race(rng, bet):
    return rules.settle_race(rng.randint(0, 4), rng.randint(0, 4), bet)


def r_wheel(rng, bet):
    return rules.settle_wheel(rng.randrange(len(rules.WHEEL_SEGMENTS)), bet)


def r_scratch(rng, bet):
    mult = rules.scratch_roll(rng)
    win_sym, _cells = rules.scratch_grid(mult, rng)
    return rules.settle_scratch(mult, win_sym, bet)


def _crash(rng, bet, target, edge=rules.CRASH_EDGE):
    crash = rules.crash_point(rng, edge)
    return rules.settle_crash(target if crash >= target else None, crash, bet)


def r_plinko(risk):
    return lambda rng, bet: rules.settle_plinko(rules.plinko_path(rng), risk, bet)


def r_mines(mines, picks, edge=rules.MINES_EDGE):
    """A bot that opens `picks` cells and then cashes out."""
    def play(rng, bet):
        layout = rules.mines_layout(mines, rng)
        boom = any(i in layout for i in rng.sample(range(rules.MINES_CELLS), picks))
        if boom:
            return rules.settle_mines(0, bet, boom=True)
        return rules.settle_mines(rules.mines_multiplier(picks, mines, edge=edge), bet)
    return play


def r_hilo(rng, bet, steps=3, edge=rules.HILO_EDGE):
    """A bot that always takes the likelier side and stops after `steps` wins."""
    deck = rules.new_deck_hilo(rng)
    current = deck.pop()
    probs = []
    for _ in range(steps):
        up = rules.hilo_prob(deck, current[0], True)
        down = rules.hilo_prob(deck, current[0], False)
        higher, p = up >= down, max(up, down)
        if p <= 0:
            break
        nxt = rules.hilo_draw(deck, current[0])
        if nxt is None:
            break
        if rules.hilo_beats(nxt, current) != higher:
            return rules.settle_hilo(None, bet, f'You guessed {"higher" if higher else "lower"}, '
                                                f'but the card was {nxt[0]}{nxt[1]}')
        probs.append(p)
        current = nxt
    return rules.settle_hilo(rules.hilo_multiplier(probs, edge=edge), bet)


def r_keno(rng, bet):
    """A bot that quick-picks KENO_PICK numbers and takes whatever the draw gives."""
    picked = rng.sample(range(1, rules.KENO_POOL + 1), rules.KENO_PICK)
    return rules.settle_keno(rules.keno_hits(picked, rules.keno_draw(rng)), bet)


# name -> (game key, round function)
ROUNDS = {
    'coin': ('coin', r_coin), 'dice': ('dice', r_dice), 'roulette (black)': ('roulette', r_roulette),
    'roulette (black + number)': ('roulette', r_roulette_number), 'blackjack (hit < 17)': ('blackjack', r_blackjack),
    'slot': ('slot', r_slot), 'lotto': ('tombala', r_lotto), 'poker (keep pairs)': ('poker', r_poker),
    'baccarat (player)': ('baccarat', r_baccarat), 'race': ('race', r_race), 'wheel': ('wheel', r_wheel),
    'scratch': ('scratch', r_scratch), 'crash @1.5x': ('crash', lambda rng, b: _crash(rng, b, 1.5)),
    'crash @2x': ('crash', lambda rng, b: _crash(rng, b, 2.0)), 'crash @5x': ('crash', lambda rng, b: _crash(rng, b, 5.0)),
    'plinko low': ('plinko', r_plinko('low')), 'plinko medium': ('plinko', r_plinko('medium')),
    'plinko high': ('plinko', r_plinko('high')),
    'mines (3 picks)': ('mines', r_mines(5, 3)), 'mines (6 picks)': ('mines', r_mines(5, 6)),
    'hi-lo (3 guesses)': ('hilo', r_hilo), 'keno (10 picks)': ('keno', r_keno),
}
EXACT = {'lotto': rules.lotto_rtp(), 'slot': rules.slot_rtp(), 'wheel': rules.wheel_rtp(), 'scratch': rules.scratch_rtp(),
         'plinko low': rules.plinko_rtp('low'), 'plinko medium': rules.plinko_rtp('medium'),
         'plinko high': rules.plinko_rtp('high'), 'crash @1.5x': rules.crash_rtp(), 'crash @2x': rules.crash_rtp(),
         'crash @5x': rules.crash_rtp(), 'mines (3 picks)': rules.mines_rtp(), 'mines (6 picks)': rules.mines_rtp(),
         'hi-lo (3 guesses)': rules.hilo_rtp(), 'keno (10 picks)': rules.keno_rtp()}


def build_rounds(edge=None):
    """ROUNDS, with the three edge-based games (Crash, Mines, Hi-Lo) priced for a difficulty's
    house edge. Everything else pays the same on every difficulty."""
    if edge is None:
        return ROUNDS
    out = dict(ROUNDS)
    out['crash @1.5x'] = ('crash', lambda rng, b: _crash(rng, b, 1.5, edge))
    out['crash @2x'] = ('crash', lambda rng, b: _crash(rng, b, 2.0, edge))
    out['crash @5x'] = ('crash', lambda rng, b: _crash(rng, b, 5.0, edge))
    out['mines (3 picks)'] = ('mines', r_mines(5, 3, edge))
    out['mines (6 picks)'] = ('mines', r_mines(5, 6, edge))
    out['hi-lo (3 guesses)'] = ('hilo', lambda rng, b: r_hilo(rng, b, 3, edge))
    return out


def exact_rtp(edge=None):
    """The exact, closed-form RTPs for a difficulty (the measured ones are just a check)."""
    if edge is None:
        return EXACT
    return {**EXACT, 'crash @1.5x': rules.crash_rtp(edge), 'crash @2x': rules.crash_rtp(edge),
            'crash @5x': rules.crash_rtp(edge), 'mines (3 picks)': rules.mines_rtp(edge),
            'mines (6 picks)': rules.mines_rtp(edge), 'hi-lo (3 guesses)': rules.hilo_rtp(edge)}


def cmd_rtp(args):
    rng = random.Random(args.seed)
    bet = 100                           # a round bet keeps integer rounding from skewing small payouts
    diff = getattr(args, 'difficulty', 'normal')
    edge = config.DIFFICULTIES[diff]['edge']
    rounds, exact = build_rounds(edge), exact_rtp(edge)
    print(f'Return to player, {args.rounds:,} rounds each, bet {bet} TL (100% = fair, below = the house wins)')
    print(f'difficulty: {config.DIFFICULTIES[diff]["name"]}  -  Crash, Mines and Hi-Lo pay back '
          f'{(1 - edge) * 100:.0f}% here\n')
    print(f'{"game / strategy":28s} {"RTP":>8s} {"±":>6s} {"exact":>8s} {"win rate":>9s}')
    for name, (_key, play) in rounds.items():
        returns, wins = [], 0
        for _ in range(args.rounds):
            delta, win, _text, _tags = play(rng, bet)
            returns.append((bet + delta) / bet)
            wins += win is True
        mean = statistics.fmean(returns)
        err = statistics.pstdev(returns) / math.sqrt(args.rounds)
        line = f'{name:28s} {mean * 100:7.2f}% {err * 100:5.2f}%'
        if name in exact:
            line += f' {exact[name] * 100:7.2f}%'
            if abs(mean - exact[name]) > 4 * err + 0.005:
                line += '   <-- does not match!'      # a measured value that drifts off its price
        else:
            line += '        -'
        print(line + f' {wins / args.rounds * 100:8.1f}%')


# =============================================================== bots that play whole runs
PROFILES = {
    'worker': dict(work=1.0, games=0, frac=0.0, pool=[], borrow=False, shop=True),
    'cautious': dict(work=0.7, games=3, frac=0.02, borrow=False, shop=True,
                     pool=['coin', 'dice', 'roulette (black)', 'plinko low', 'crash @1.5x']),
    'gambler': dict(work=0.3, games=5, frac=0.25, borrow=True, shop=False,
                    pool=['slot', 'lotto', 'keno (10 picks)', 'wheel', 'scratch', 'crash @2x',
                          'plinko high', 'coin']),
    'highroller': dict(work=0.2, games=3, frac=0.5, borrow=True, shop=False,
                       pool=['crash @2x', 'blackjack (hit < 17)', 'plinko medium', 'roulette (black)']),
}
SHOP_ORDER = ['course', 'pet', 'car', 'apartment', 'advisor', 'vip']
ENDING_ORDER = ['high_roller', 'hollow', 'reformed', 'breakdown', 'bankrupt', 'debt_spiral', 'timeout']


class Bot:
    def __init__(self, engine, rng, profile):
        self.e, self.s, self.rng, self.p = engine, engine.state, rng, profile
        self.rounds = build_rounds(engine.state.diff.get('edge'))     # this difficulty's house edge

    def play_round(self):
        s = self.s
        pool = [n for n in self.p['pool'] if s.level >= config.UNLOCK[ROUNDS[n][0]]]
        if not pool or s.balance < 1:
            return False
        key, play = self.rounds[self.rng.choice(pool)]
        bet = max(1, min(s.balance, s.max_bet, int(s.balance * self.p['frac'])))
        delta, win, _text, tags = play(self.rng, bet)
        self.e.settle(key, delta, win, bet, tags)
        return True

    def manage_money(self):
        e, s = self.e, self.s
        if s.debt and s.balance > s.debt * 2 + 100:
            e.repay(s.debt)
        if self.p['borrow'] and s.balance < 5 and s.credit_available >= 1:
            e.borrow(min(s.credit_available, 100 * s.level))
        if self.p['shop']:
            for key in SHOP_ORDER:
                ok, _ = e.item_status(key)
                if ok and s.balance >= e.price(key) * 1.5 + 100:
                    e.buy(key)
        if s.mental < 40 and e.item_status('therapy')[0] and s.balance > e.price('therapy') * 2:
            e.buy('therapy')
        if not self.p['borrow'] and s.balance > 600:
            e.deposit(s.balance - 300)

    def best_job(self):
        best = max((j for j in config.JOBS if j['level'] <= self.s.level), key=lambda j: j['pay'])
        if best['key'] != self.s.job:
            self.e.take_job(best['key'])

    def handle_events(self):
        e = self.e
        while e.pending_events:
            ev = e.pending_events.pop(0)
            e.run_event(ev, e.first_enabled_choice(ev))

    def one_turn(self):
        e, s, p = self.e, self.s, self.p
        self.manage_money()
        if s.mental < 35 and s.games_today == 0:
            e.pass_day()                                   # rest
        elif s.work_cooldown == 0 and self.rng.random() < p['work']:
            self.best_job()
            e.go_work()
        else:
            played = 0
            while played < p['games'] and s.games_today < 5 and self.play_round():
                played += 1
            if 0 < s.games_today < 5 or played == 0:
                e.pass_day()
        self.handle_events()


def one_run(difficulty, profile_name, seed, max_days):
    rng = random.Random(seed)
    state = GameState()
    state.set_defaults()                   # (not reset(): that would delete a real savegame.txt)
    state.start_run(difficulty)
    engine = Engine(state=state, meta=MetaState(), rng=rng, persist=False)
    bot = Bot(engine, rng, PROFILES[profile_name])
    ending = None
    while state.day < max_days:
        bot.one_turn()
        ending = engine.check_endings()
        if ending:
            break
    return ending or 'timeout', state.day, state.net_worth, state.level


def cmd_run(args):
    diffs = list(config.DIFFICULTIES) if args.difficulty == 'all' else [args.difficulty]
    bots = list(PROFILES) if args.bots == 'all' else args.bots.split(',')
    for d in diffs:
        print(f'\n=== {config.DIFFICULTIES[d]["name"].upper()}  (goal {config.DIFFICULTIES[d]["goal"]:,} TL, '
              f'{args.runs} runs per bot, up to {args.days} days) ===')
        print(f'{"bot":11s}' + ''.join(f'{k.replace("_", " "):>12s}' for k in ENDING_ORDER)
              + f'{"med. day":>10s}{"med. worth":>12s}{"med. level":>11s}')
        for b in bots:
            results = [one_run(d, b, args.seed * 100_003 + i, args.days) for i in range(args.runs)]
            counts = Counter(r[0] for r in results)
            row = ''.join(f'{counts[k] / args.runs * 100:11.0f}%' for k in ENDING_ORDER)
            print(f'{b:11s}{row}{statistics.median(r[1] for r in results):10.0f}'
                  f'{statistics.median(r[2] for r in results):12,.0f}{statistics.median(r[3] for r in results):11.0f}')
            goal_days = sorted(r[1] for r in results if r[0] in ('high_roller', 'hollow'))
            if goal_days:
                q = lambda f: goal_days[min(len(goal_days) - 1, int(len(goal_days) * f))]   # noqa: E731
                print(f'{"":11s}  days to the goal: fastest {goal_days[0]}, 25% {q(0.25)}, median {q(0.5)}, '
                      f'75% {q(0.75)}, slowest {goal_days[-1]}')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    r = sub.add_parser('rtp', help='return-to-player of every game')
    r.add_argument('--rounds', type=int, default=200_000)
    r.add_argument('--seed', type=int, default=1)
    r.add_argument('--difficulty', default='normal', choices=list(config.DIFFICULTIES),
                   help='Crash, Mines and Hi-Lo are priced for this difficulty')
    run = sub.add_parser('run', help='play whole runs with bots')
    run.add_argument('--difficulty', default='all', choices=['all'] + list(config.DIFFICULTIES))
    run.add_argument('--bots', default='all', help='comma list of: ' + ', '.join(PROFILES))
    run.add_argument('--runs', type=int, default=200)
    run.add_argument('--days', type=int, default=600)
    run.add_argument('--seed', type=int, default=1)
    args = ap.parse_args()
    {'rtp': cmd_rtp, 'run': cmd_run}[args.cmd](args)


if __name__ == '__main__':
    main()
