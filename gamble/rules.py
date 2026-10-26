"""Pure game maths: dealing, hand values and payouts. No Qt and no game state in here.

Every settle_* function returns (delta, win, text, tags):
  delta = net change of the wallet, win = True / False / None (push), tags = achievement hints.
The GUI and the balance simulator both use these, so they can never disagree about the rules.
"""
import math
from collections import Counter

SUITS = ['♠', '♥', '♦', '♣']
RED = {'♥', '♦'}


def _result(delta, win, text, tags=()):
    return delta, win, text, tags


# ---------------------------------------------------------------- coin and dice
def coin_flip(rng):
    return rng.choice('ht')


def settle_coin(guess, result, bet):
    name = 'Heads' if result == 'h' else 'Tails'
    if guess == result:
        return _result(bet, True, f'Result: {name}. Congratulations! You won.')
    return _result(-bet, False, f'Result: {name}. You lost.')


def settle_dice(guess, roll, bet):
    if guess == roll:
        return _result(bet * 4, True, f'Dice: {roll}. Congratulations! You won.')
    return _result(-bet, False, f'Dice: {roll}. You lost.')


# ---------------------------------------------------------------- roulette
def roulette_table(rng):
    nums = list(range(1, 11))
    rng.shuffle(nums)
    return sorted([(n, 'black') for n in nums[:4]] + [(n, 'red') for n in nums[4:8]]
                  + [(n, 'green') for n in nums[8:]])


def settle_roulette(color_guess, number_guess, result, bet):
    rn, rc = result
    head = f'Roulette result: {rn} {rc}.'
    green = color_guess == 'green'
    if number_guess is None:
        if color_guess == rc:
            return _result(bet * 2 if green else bet, True,
                           f"{head} Congratulations! You won {'3x' if green else '2x'} your bet.")
        return _result(-bet, False, f'{head} You lost.')
    if color_guess == rc and number_guess == rn:
        return _result(bet * 3 if green else bet * 2, True,
                       f"{head} Congratulations! You won {'4x' if green else '3x'} your bet.")
    if color_guess == rc:
        return _result(bet * 2 if green else bet, True,
                       f"{head} You didn't guess the number, but you guessed the color! "
                       f"You won {'3x' if green else '2x'} your bet.")
    return _result(-bet, False, f'{head} You lost.')


# ---------------------------------------------------------------- blackjack
BJ_RANKS = [('2', 2), ('3', 3), ('4', 4), ('5', 5), ('6', 6), ('7', 7), ('8', 8), ('9', 9),
            ('10', 10), ('J', 10), ('Q', 10), ('K', 10), ('A', 11)]


def new_deck_bj(rng):
    deck = [(label, value, suit) for suit in SUITS for label, value in BJ_RANKS]
    rng.shuffle(deck)
    return deck


def bj_value(hand):
    value = sum(c[1] for c in hand)
    aces = sum(1 for c in hand if c[1] == 11)
    while value > 21 and aces:
        value -= 10
        aces -= 1
    return value


def settle_bust(bet):
    return _result(-bet, False, 'Bust! You lost.')


def settle_blackjack(player, dealer, bet):
    pt, dt = bj_value(player), bj_value(dealer)
    if pt > 21:                                  # the player busted - the dealer never gets to lose
        return settle_bust(bet)
    if dt > 21 or pt > dt:
        if pt == 21 and len(player) == 2:
            return _result(int(bet * 1.5), True, 'You win! Blackjack! You win 1.5x your bet.', ('natural',))
        return _result(bet, True, 'You win!')
    if pt < dt:
        return _result(-bet, False, 'Dealer wins. You lost.')
    return _result(0, None, 'Push! (Draw)')


# ---------------------------------------------------------------- slot machine
SLOT_PAYOUT = {'three_same': 5, 'two_same': 1.5}   # 5 symbols -> average payout 92%
SLOT_KEYS = 'ABCDE'


def slot_spin(rng):
    return [rng.choice(SLOT_KEYS) for _ in range(3)]


def settle_slot(reels, bet):
    if reels[0] == reels[1] == reels[2]:
        mult = SLOT_PAYOUT['three_same']
        return _result(bet * (mult - 1), True, f'JACKPOT! You won {mult}x your bet!', ('jackpot',))
    if len(set(reels)) == 2:
        delta = int(bet * SLOT_PAYOUT['two_same']) - bet
        if delta > 0:
            return _result(delta, True, f"Nice! You won {SLOT_PAYOUT['two_same']:g}x your bet!")
        return _result(0, None, 'Two match! Your bet is returned.')
    return _result(-bet, False, 'No match. You lost.')


# ---------------------------------------------------------------- lotto
LOTTO_POOL = 30                                       # you pick 6 numbers out of 30, the draw is 6 out of 30
LOTTO_PAYOUT = {2: 1, 3: 5, 4: 35, 5: 200, 6: 2000}   # matches -> total return (average payout ~90%)


def lotto_draw(rng):
    return sorted(rng.sample(range(1, LOTTO_POOL + 1), 6))


def settle_lotto(matches, bet):
    head = f'Matched numbers: {matches}.'
    mult = LOTTO_PAYOUT.get(matches, 0)
    if matches >= 5:
        return _result(bet * (mult - 1), True, f'{head} JACKPOT! You won {mult}x your bet!', ('jackpot', 'lotto4'))
    if matches >= 3:
        return _result(bet * (mult - 1), True, f'{head} Nice! You won {mult}x your bet!',
                       ('lotto4',) if matches == 4 else ())
    if matches == 2:
        return _result(0, None, f'{head} Your bet is returned.')
    return _result(-bet, False, f'{head} No big win. You lost.')


# ---------------------------------------------------------------- keno
# Pick KENO_PICK numbers out of KENO_POOL; the draw takes KENO_DRAW of them. The house edge comes
# from the shape of the hypergeometric distribution, so the payout table below can be priced exactly
# (see keno_rtp) instead of being guessed - it returns 90.05% of every stake.
KENO_POOL = 40
KENO_PICK = 10
KENO_DRAW = 10
KENO_PAYOUT = {3: 1, 4: 1.5, 5: 4, 6: 20, 7: 120, 8: 700, 9: 3500, 10: 20000}


def keno_draw(rng):
    return sorted(rng.sample(range(1, KENO_POOL + 1), KENO_DRAW))


def keno_hits(picked, drawn):
    return len(set(picked) & set(drawn))


def keno_hit_prob(hits):
    """Chance of matching exactly `hits` numbers with KENO_PICK picks."""
    return (math.comb(KENO_PICK, hits) * math.comb(KENO_POOL - KENO_PICK, KENO_DRAW - hits)
            / math.comb(KENO_POOL, KENO_DRAW))


def keno_rtp():
    return sum(keno_hit_prob(h) * m for h, m in KENO_PAYOUT.items())


def settle_keno(hits, bet):
    head = f'{hits} of your {KENO_PICK} numbers hit.'
    mult = KENO_PAYOUT.get(hits, 0)
    if mult >= 20:
        return _result(int(bet * (mult - 1)), True, f'{head} JACKPOT! You won {mult:g}x your bet!',
                       ('jackpot',))
    if mult > 1:
        delta = int(bet * (mult - 1))
        if delta >= 1:                          # tiny stakes can round a win down to nothing
            return _result(delta, True, f'{head} You won {mult:g}x your bet!')
        return _result(0, None, f'{head} Your bet is returned.')
    if mult == 1:
        return _result(0, None, f'{head} Your bet is returned.')
    return _result(-bet, False, f'{head} Not enough. You lost.')


# ---------------------------------------------------------------- poker (5 card draw vs computer)
POKER_NAMES = ['High Card', 'One Pair', 'Two Pair', 'Three of a Kind', 'Straight', 'Flush',
               'Full House', 'Four of a Kind', 'Straight Flush']
RANK_STR = {11: 'J', 12: 'Q', 13: 'K', 14: 'A'}


def new_deck_poker(rng):
    deck = [(r, s) for r in range(2, 15) for s in SUITS]
    rng.shuffle(deck)
    return deck


def poker_hand_rank(hand):
    values = sorted([card[0] for card in hand], reverse=True)
    suits = [card[1] for card in hand]
    value_counts = {v: values.count(v) for v in set(values)}
    is_flush = len(set(suits)) == 1
    is_straight = all(values[i] - 1 == values[i + 1] for i in range(4))
    if not is_straight and set(values) == {14, 2, 3, 4, 5}:
        is_straight = True                       # the wheel A-2-3-4-5 plays as a five-high straight
        values = [5, 4, 3, 2, 1]
    counts = sorted(value_counts.values(), reverse=True)
    if is_straight and is_flush:
        return (8, values)
    if 4 in counts:
        return (7, values)
    if 3 in counts and 2 in counts:
        return (6, values)
    if is_flush:
        return (5, values)
    if is_straight:
        return (4, values)
    if 3 in counts:
        return (3, values)
    if counts.count(2) == 2:
        return (2, values)
    if 2 in counts:
        return (1, values)
    return (0, values)


def keep_indices(hand):
    """The standard 'sensible' draw: keep pairs or better, otherwise keep the two highest cards."""
    counts = Counter(c[0] for c in hand)
    keep = [i for i, c in enumerate(hand) if counts[c[0]] >= 2]
    return keep or sorted(range(5), key=lambda i: -hand[i][0])[:2]


def computer_draw(computer, deck, rng=None):
    """The computer plays the sensible draw (it used to swap random cards, which lost 70% of the time)."""
    keep = set(keep_indices(computer))
    for i in range(5):
        if i not in keep:
            computer[i] = deck.pop()


POKER_WIN = 0.9      # a win pays 1.9x, a draw returns the bet


def settle_poker(player_rank, computer_rank, bet):
    if player_rank > computer_rank:
        delta = int(bet * POKER_WIN)
        if delta > 0:
            return _result(delta, True, 'You win! (pays 1.9x)')
        return _result(0, None, 'You win, but the payout rounds down to nothing. Bet returned.')
    if player_rank < computer_rank:
        return _result(-bet, False, 'Computer wins. You lost.')
    return _result(0, None, 'Draw! Bet returned.')


# ---------------------------------------------------------------- baccarat
BAC_RANKS = [('A', 1), ('2', 2), ('3', 3), ('4', 4), ('5', 5), ('6', 6), ('7', 7), ('8', 8), ('9', 9),
             ('10', 0), ('J', 0), ('Q', 0), ('K', 0)]


def new_deck_bac(rng):
    deck = [(label, value, suit) for suit in SUITS for label, value in BAC_RANKS]
    rng.shuffle(deck)
    return deck


BAC_WIN = 0.9          # a win pays 1.9x, a tie returns the bet


def bac_total(cards):
    return sum(c[1] for c in cards) % 10


def settle_baccarat(who, player_total, banker_total, bet):
    winner = 'player' if player_total > banker_total else 'banker' if banker_total > player_total else 'tie'
    if winner == 'tie':
        return _result(0, None, "It's a tie! Bet returned.")
    if winner == who:
        delta = int(bet * BAC_WIN)
        if delta > 0:
            return _result(delta, True, f'You win! ({winner.capitalize()} wins, pays 1.9x)')
        return _result(0, None, 'You win, but the payout rounds down to nothing. Bet returned.')
    return _result(-bet, False, f'You lost! ({winner.capitalize()} wins)')


# ---------------------------------------------------------------- horse race
RACE_NAMES = ['Horse1', 'Horse2', 'Horse3', 'Horse4', 'Horse5']


def settle_race(pick, winner, bet):
    head = f'Race result: Winner is {winner + 1}-{RACE_NAMES[winner]}.'
    if pick == winner:
        return _result(bet * 3, True, f'{head} Congratulations! You won 4x your bet!')
    return _result(-bet, False, f'{head} You lost.')


# ---------------------------------------------------------------- wheel of fortune
WHEEL_SEGMENTS = [0, 2, 0, 0.5, 0, 3, 0, 1, 0, 4, 0.5, 0]   # 12 slices, average payout ~92%
WHEEL_LABELS = {0: '0×', 0.5: '½×', 1: '1×', 2: '2×', 3: '3×', 4: '4×'}


def settle_wheel(segment, bet):
    m = WHEEL_SEGMENTS[segment]
    payout = int(bet * m)
    delta = payout - bet
    head = f'The wheel landed on {WHEEL_LABELS[m]}.'
    if delta > 0:
        return _result(delta, True, f'{head} You won {m:g}x your bet!')
    if delta == 0:
        return _result(0, None, f'{head} Your bet is returned.')
    if payout > 0:
        return _result(delta, False, f'{head} You get half of your bet back.')
    return _result(delta, False, f'{head} You lost.')


# ---------------------------------------------------------------- scratch card
SCRATCH_SYMBOLS = {'🍒': 1, '🍀': 2, '🔔': 3, '⭐': 5, '💎': 10}      # symbol -> prize multiplier
SCRATCH_ODDS = [(0, 0.635), (1, 0.14), (2, 0.11), (3, 0.06), (5, 0.04), (10, 0.015)]   # average payout ~89%


def scratch_roll(rng):
    return rng.choices([m for m, _ in SCRATCH_ODDS], [w for _, w in SCRATCH_ODDS])[0]


def scratch_grid(mult, rng):
    """Returns (winning symbol or None, 9 cells). A win has exactly one triple, a loss has none."""
    symbols = list(SCRATCH_SYMBOLS) + ['🍋']
    if mult:
        win_sym = next(sym for sym, m in SCRATCH_SYMBOLS.items() if m == mult)
        pool = [sym for sym in symbols if sym != win_sym] * 2
        rng.shuffle(pool)
        cells = [win_sym] * 3 + pool[:6]
    else:
        win_sym = None
        pool = symbols * 2
        rng.shuffle(pool)
        cells = pool[:9]
    rng.shuffle(cells)
    return win_sym, cells


def settle_scratch(mult, win_sym, bet):
    payout = int(bet * mult)
    delta = payout - bet
    if mult == 0:
        return _result(-bet, False, 'No match. You lost.')
    if delta > 0:
        return _result(delta, True, f'Three {win_sym}! You won {mult}x your bet!', ('jackpot',) if mult >= 10 else ())
    return _result(0, None, f'Three {win_sym}! Your bet is returned.')


# ---------------------------------------------------------------- crash
CRASH_EDGE = 0.08          # house edge -> every cash-out target returns 92% on average


def crash_point(rng, edge=CRASH_EDGE):
    """The multiplier where the round crashes. P(crash >= x) = (1 - edge) / x for every x > 1,
    and 8% of rounds crash instantly at 1.00x."""
    u = rng.random()
    c = math.floor(100 * (1 - edge) / (1 - u)) / 100
    return min(max(c, 1.0), 1000.0)


def settle_crash(cashed, crash, bet):
    """cashed = the multiplier you cashed out at (None if you didn't)."""
    if cashed is None or crash <= 1.0 or cashed > crash:
        return _result(-bet, False, f'Crashed at {crash:.2f}×! You lost.')
    payout = int(bet * cashed)
    delta = payout - bet
    tags = (('crash_5x',) if cashed >= 5 else ()) + (('jackpot',) if cashed >= 25 else ())
    if delta > 0:
        return _result(delta, True, f'Cashed out at {cashed:.2f}×! You won.', tags)
    return _result(0, None, f'Cashed out at {cashed:.2f}×. Your bet is returned.')


# ---------------------------------------------------------------- plinko
PLINKO_ROWS = 8
PLINKO_TABLES = {      # 9 slots, left to right; every table returns about 92% on average
    'low': [3.0, 1.6, 1.15, 0.9, 0.55, 0.9, 1.15, 1.6, 3.0],
    'medium': [9, 3, 1.2, 0.7, 0.35, 0.7, 1.2, 3, 9],
    'high': [20, 4.5, 1.15, 0.4, 0.2, 0.4, 1.15, 4.5, 20],
}


def plinko_path(rng):
    """True = the ball bounced to the right at that row."""
    return [rng.random() < 0.5 for _ in range(PLINKO_ROWS)]


def settle_plinko(path, risk, bet):
    slot = sum(path)
    m = PLINKO_TABLES[risk][slot]
    payout = int(bet * m)
    delta = payout - bet
    head = f'The ball landed in the {m:g}× slot.'
    tags = (('edge',) if slot in (0, PLINKO_ROWS) else ()) + (('jackpot',) if m >= 20 else ())
    if delta > 0:
        return _result(delta, True, f'{head} You won {m:g}x your bet!', tags)
    if delta == 0:
        return _result(0, None, f'{head} Your bet is returned.', tags)
    if payout > 0:
        return _result(delta, False, f'{head} You get some of your bet back.', tags)
    return _result(delta, False, f'{head} You lost.', tags)


# ---------------------------------------------------------------- mines
MINES_CELLS = 25                                   # the board is 5 x 5
MINES_RISK = {'low': 3, 'medium': 5, 'high': 8}    # mines hidden in the cells
MINES_EDGE = 0.08                                  # house edge -> every cash-out returns 92% on average


def mines_layout(mines, rng, cells=MINES_CELLS):
    """The cells (0..cells-1) that hide a mine."""
    return set(rng.sample(range(cells), mines))


def mines_multiplier(picks, mines, cells=MINES_CELLS, edge=MINES_EDGE):
    """Multiplier for cashing out after `picks` safe cells. Each cell you uncover is worth
    (cells-i)/(cells-mines-i), and the edge is taken once, so stopping at ANY pick pays
    (1 - edge) - 92% on Normal, 95% on Easy, 88% on Hard."""
    picks = max(0, min(picks, cells - mines))
    m = 1.0
    for i in range(picks):
        m *= (cells - i) / (cells - mines - i)
    return max(1.0, round((1 - edge) * m, 2))


def settle_mines(mult, bet, boom=False, cleared=False):
    """mult = the multiplier you cashed out at. boom = you stepped on a mine instead."""
    if boom:
        return _result(-bet, False, 'Boom! You hit a mine. You lost.')
    payout = int(bet * mult)
    delta = payout - bet
    head = 'You cleared the whole board!' if cleared else f'You cashed out at {mult:g}x.'
    tags = (('jackpot',) if mult >= 20 else ()) + (('board_clear',) if cleared else ())
    if delta > 0:
        return _result(delta, True, f'{head} You won {mult:g}x your bet!', tags)
    return _result(0, None, f'{head} Your bet is returned.', tags)


# ---------------------------------------------------------------- hi-lo
HILO_EDGE = 0.08                                   # house edge -> every cash-out returns 92% on average
HILO_ORDER = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']   # A counts high


def new_deck_hilo(rng):
    deck = [(label, suit) for suit in SUITS for label in HILO_ORDER]
    rng.shuffle(deck)
    return deck


def hilo_beats(a, b):
    """True when card `a` ranks above card `b`."""
    return HILO_ORDER.index(a[0]) > HILO_ORDER.index(b[0])


def hilo_prob(deck, current, higher):
    """Chance that the next card beats `current` drawing from `deck`. Ties are re-dealt, so the
    odds are conditional on the next card having a different rank. 0 = the guess cannot win."""
    wins = losses = 0
    for label, _ in deck:
        if label == current:
            continue
        if (HILO_ORDER.index(label) > HILO_ORDER.index(current)) == higher:
            wins += 1
        else:
            losses += 1
    return wins / (wins + losses) if wins + losses else 0.0


def hilo_draw(deck, current):
    """The next card, with ties discarded. None when the deck has nothing left."""
    while deck:
        card = deck.pop()
        if card[0] != current:
            return card
    return None


def hilo_multiplier(probs, edge=HILO_EDGE):
    """Multiplier for cashing out after winning every step in `probs` (each entry is that step's
    true chance of winning). Because the payout is one edge haircut on the fair odds, stopping
    after ANY streak - however you chose it - returns (1 - edge) of the stake on average:
    92% on Normal, 95% on Easy, 88% on Hard."""
    p = 1.0
    for w in probs:
        p *= w
    if p <= 0:
        return 1.0
    return max(1.0, round((1 - edge) / p, 2))


def settle_hilo(mult, bet, head='Wrong guess', steps=0):
    """mult = the multiplier you cashed out at, or None when the guess lost.
    `steps` = how many guesses were won in a row (feeds the streak achievements)."""
    if mult is None:
        return _result(-bet, False, f'{head}. You lost.', ('hilo_7',) if steps >= 7 else ())
    payout = int(bet * mult)
    delta = payout - bet
    tags = (('jackpot',) if mult >= 20 else ()) + (('hilo_7',) if steps >= 7 else ())
    if delta > 0:
        return _result(delta, True, f'Cashed out at {mult:g}x! You won {mult:g}x your bet!', tags)
    return _result(0, None, f'Cashed out at {mult:g}x. Your bet is returned.', tags)


# ---------------------------------------------------------------- exact expected returns (for tests/simulator)
def slot_rtp():
    total = 0
    for a in SLOT_KEYS:
        for b in SLOT_KEYS:
            for c in SLOT_KEYS:
                if a == b == c:
                    total += SLOT_PAYOUT['three_same']
                elif len({a, b, c}) == 2:
                    total += SLOT_PAYOUT['two_same']
    return total / len(SLOT_KEYS) ** 3


def wheel_rtp():
    return sum(WHEEL_SEGMENTS) / len(WHEEL_SEGMENTS)


def scratch_rtp():
    return sum(m * p for m, p in SCRATCH_ODDS)


def plinko_rtp(risk):
    return sum(math.comb(PLINKO_ROWS, k) / 2 ** PLINKO_ROWS * m for k, m in enumerate(PLINKO_TABLES[risk]))


def lotto_rtp():
    total = math.comb(LOTTO_POOL, 6)
    return sum(math.comb(6, k) * math.comb(LOTTO_POOL - 6, 6 - k) / total * m for k, m in LOTTO_PAYOUT.items())


def crash_rtp(edge=CRASH_EDGE):
    return 1 - edge


def mines_rtp(edge=MINES_EDGE):
    return 1 - edge


def hilo_rtp(edge=HILO_EDGE):
    return 1 - edge


# ---------------------------------------------------------------- what the help page shows (D8)
# Closed-form where one exists, otherwise the value measured by `python simulate.py rtp`.
FIXED_RTP = {'coin': 1.0, 'dice': 0.8333, 'roulette': 0.80, 'blackjack': 0.94, 'poker': 0.95,
             'baccarat': 0.955, 'race': 0.80}
RTP_NOTES = {'coin': 'exactly fair - the only one',
             'roulette': '80% on colours, 90% with a number bet. Green is the sucker bet: 60% / 70%',
             'blackjack': 'with basic strategy', 'poker': 'with the suggested holds',
             'plinko': 'low / medium / high risk', 'crash': 'follows the difficulty'}


def game_rtp(key, edge=HILO_EDGE, risk='medium'):
    """The share of every stake a game gives back on average (1.0 = fair, below = the house wins).

    Crash, Mines and Hi-Lo follow the difficulty's house edge; everything else is fixed."""
    if key in ('crash', 'mines', 'hilo'):
        return 1 - edge
    if key == 'plinko':
        return plinko_rtp(risk)
    if key == 'slot':
        return slot_rtp()
    if key == 'wheel':
        return wheel_rtp()
    if key == 'scratch':
        return scratch_rtp()
    if key == 'tombala':
        return lotto_rtp()
    if key == 'keno':
        return keno_rtp()
    return FIXED_RTP.get(key, 0.0)
