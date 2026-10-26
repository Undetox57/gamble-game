"""Table and betting games: roulette, blackjack, poker, lotto, baccarat, horse race."""
import math

from PyQt6.QtCore import QPointF, QPoint, QRectF, Qt, QTimer
from PyQt6.QtGui import QColor, QConicalGradient, QLinearGradient, QPainter, QPen, QPolygonF
from PyQt6.QtWidgets import QGridLayout, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from .. import rules
from ..fx import VRNG, fade_flip, fade_in
from ..widgets import AC, Button, CardRow, centered, paint, paint_card
from .base import BaseGame, K, digit_key

CHIP_COLORS = {'black': '#1a1a1a', 'red': '#c62828', 'green': '#2e9e5b'}


def lighten(hex_color, amount=1.6):
    """A lighter shade of #rrggbb, for gradient tops."""
    r, g, b = (int(hex_color[i:i + 2], 16) for i in (1, 3, 5))
    return '#%02x%02x%02x' % tuple(min(255, int(c * amount)) for c in (r, g, b))


def chip_style(color, hi=False):
    c = CHIP_COLORS[color]
    light = lighten(c, 1.7 if color != 'black' else 3.2)
    return (f"background:qradialgradient(cx:0.35, cy:0.3, radius:0.9, stop:0 {light}, stop:1 {c});"
            f"color:white;border:{5 if hi else 2}px solid "
            f"{'#f4c542' if hi else '#666666'};border-radius:26px;font-size:18px;font-weight:700;")


class RouletteGame(BaseGame):
    key, title = 'roulette', 'Roulette'

    def build(self):
        self.table = rules.roulette_table(self.rng)
        self.body.addWidget(centered('Number-color table (randomized this round)', 'hint'))
        chips = QHBoxLayout()
        chips.setAlignment(AC)
        self.chips = {}
        for n, c in self.table:
            lbl = QLabel(str(n))
            lbl.setFixedSize(52, 52)
            lbl.setAlignment(AC)
            lbl.setStyleSheet(chip_style(c))
            chips.addWidget(lbl)
            self.chips[n] = (lbl, c)
        self.body.addLayout(chips)
        self.body.addStretch()
        # stage 1: color
        self.color_box = QWidget()
        cl = QVBoxLayout(self.color_box)
        cl.addWidget(centered('Choose a color', 'prompt'))
        row = QHBoxLayout()
        for c, label, key in (('black', 'Black  (2×)  [B]', K.Key_B), ('red', 'Red  (2×)  [R]', K.Key_R),
                              ('green', 'Green  (3×)  [G]', K.Key_G)):
            b = Button(label)
            b.setMinimumHeight(48)
            b.clicked.connect(lambda _=False, c=c: self.choose_color(c))
            row.addWidget(b)
            self.bind(key, b)
        cl.addLayout(row)
        self.body.addWidget(self.color_box)
        # stage 2: optional number
        self.num_box = QWidget()
        self.num_box.hide()
        self.num_lay = QVBoxLayout(self.num_box)
        self.body.addWidget(self.num_box)
        self.body.addStretch()

    def choose_color(self, color):
        self.color = color
        self.color_box.hide()
        self.num_lay.addWidget(centered(f'You chose {color}. Guess a number as well? (optional, pays more)', 'prompt'))
        row = QHBoxLayout()
        for n, c in self.table:
            if c == color:
                b = Button(f'{n}  [{n % 10}]')
                b.setMinimumHeight(46)
                b.clicked.connect(lambda _=False, n=n: self.spin(n))
                row.addWidget(b)
                self.bind(digit_key(n % 10), b)
        skip = Button('Skip (color only)  [Space]')
        skip.setObjectName('primary')
        skip.setMinimumHeight(46)
        skip.clicked.connect(lambda: self.spin(None))
        row.addWidget(skip)
        self.bind(K.Key_Space, skip)
        self.num_lay.addLayout(row)
        self.num_box.show()

    def spin(self, number_guess):
        if self.in_progress:
            return
        self.num_box.hide()
        self.lock(True)
        result = self.rng.choice(self.table)
        prev = {'n': None}

        def hi(n):
            if prev['n'] is not None:
                lbl, c = self.chips[prev['n']]
                lbl.setStyleSheet(chip_style(c))
            lbl, c = self.chips[n]
            lbl.setStyleSheet(chip_style(c, True))
            prev['n'] = n

        def done():
            hi(result[0])
            if self.color == result[1] or (number_guess is not None and number_guess == result[0]):
                chip = self.chips[result[0]][0]
                self.burst_on(chip, 0.5, 0.3, n=16, colors=['#f4c542', '#ffe9a3'],
                              speed=(1.2, 3.6), gravity=0.28, size=(3, 6))
            self.finish_with(rules.settle_roulette(self.color, number_guess, result, self.bet))
        self.animate(20, 80, lambda n: hi(VRNG.randint(1, 10)), done)


class BlackjackGame(BaseGame):
    """Split and Double Down on top of the classic single-hand game.

    Every extra hand carries its own stake; the whole round still settles once, so the stats,
    the streaks and the profit tracking see exactly one played game - as before."""

    key, title = 'blackjack', 'Blackjack'

    def build(self):
        self.deck = rules.new_deck_bj(self.rng)
        self.hands = [[self.deck.pop(), self.deck.pop()]]
        self.stakes = [self.bet]                 # what each hand has at risk
        self.first_move = [True]                 # Double is offered only before the first action
        self.sitting = [False]                   # a hand that stood or busted
        self.split_aces = False                  # split aces get exactly one card each
        self.ever_split = False
        self.dealer = [self.deck.pop(), self.deck.pop()]
        self.active = 0
        self.player, self.stake = self.hands[0], self.bet
        self.playing = True
        self.lock(True)
        self.body.addWidget(centered('Dealer', 'hint'))
        self.dealer_row = CardRow()
        self.body.addWidget(self.dealer_row)
        self.dealer_total = centered('', 'prompt')
        self.body.addWidget(self.dealer_total)
        self.body.addStretch()
        self.you_lbl = centered('You', 'hint')
        self.body.addWidget(self.you_lbl)
        self.player_row = CardRow()
        self.body.addWidget(self.player_row)
        self.player_total = centered('', 'prompt')
        self.body.addWidget(self.player_total)
        row = QHBoxLayout()
        self.hit_btn = Button('Hit  [H]')
        self.stand_btn = Button('Stand  [S / Space]')
        self.split_btn = Button('Split  [P]')
        self.double_btn = Button('Double  [D]')
        for b in (self.hit_btn, self.stand_btn, self.split_btn, self.double_btn):
            b.setMinimumHeight(48)
            row.addWidget(b)
        self.hit_btn.setObjectName('primary')
        self.hit_btn.clicked.connect(self.hit)
        self.stand_btn.clicked.connect(self.stand)
        self.split_btn.clicked.connect(self.split_pair)
        self.double_btn.clicked.connect(self.double_down)
        self.body.addLayout(row)
        self.bind(K.Key_H, self.hit_btn)
        self.bind(K.Key_S, self.stand_btn)
        self.bind(K.Key_P, self.split_btn)
        self.bind(K.Key_D, self.double_btn)
        self.bind(K.Key_Space, self.stand_btn)
        self.render(False)
        self.sync_actions()

    # ---- the four actions
    def can_split(self):
        h = self.hands[self.active]
        return (self.playing and not self.sitting[self.active] and len(self.hands) < 4 and len(h) == 2
                and h[0][1] == h[1][1] and self._affordable(self.stakes[self.active]))

    def can_double(self):
        h = self.hands[self.active]
        return (self.playing and not self.sitting[self.active] and self.first_move[self.active]
                and len(h) == 2 and self._affordable(self.stakes[self.active]))

    def _affordable(self, extra):
        """The wallet must cover every stake already on the table plus `extra` more."""
        return self.app.state.balance >= sum(self.stakes) + extra

    def sync_actions(self):
        live = self.playing and not self.sitting[self.active]
        self.hit_btn.setEnabled(live)
        self.stand_btn.setEnabled(live)
        self.split_btn.setEnabled(self.can_split())
        self.double_btn.setEnabled(self.can_double())

    def hit(self):
        if not self.playing or self.sitting[self.active]:
            return
        h = self.hands[self.active]
        h.append(self.deck.pop())
        self.first_move[self.active] = False
        self.render(False)
        value = rules.bj_value(h)
        if value > 21:
            self.fx_flash('#ff6b6b', 40, 320)
            self.burst_on(self.player_row, 0.5, 0.5, n=14, colors=['#ff6b6b', '#ffb0b0'],
                          speed=(1.5, 4.5), gravity=0.2, size=(3, 6))
            self.end_hand()
        elif value == 21:
            self.end_hand()                                  # 21 is always the end of the road
        self.sync_actions()

    def stand(self):
        if not self.playing or self.sitting[self.active]:
            return
        self.end_hand()

    def double_down(self):
        if not self.can_double():
            return
        self.stakes[self.active] *= 2
        self.first_move[self.active] = False
        self.hands[self.active].append(self.deck.pop())
        self.render(False)
        if self.effects_on():
            self.burst_on(self.double_btn, 0.5, 0.5, n=12, colors=['#f4c542', '#ffe9a3'],
                          speed=(1.2, 4.0), gravity=0.2, size=(3, 6))
        self.end_hand()                                      # one card, then the hand is done

    def split_pair(self):
        if not self.can_split():
            return
        h = self.hands[self.active]
        aces = h[0][1] == 11 and h[1][1] == 11
        self.hands.append([h.pop()])                         # the second hand waits its turn
        self.stakes.append(self.stakes[self.active])
        self.first_move.append(False)
        self.sitting.append(False)
        self.ever_split = True
        self.split_aces = self.split_aces or aces
        self.first_move[self.active] = False                 # no double after a split
        h.append(self.deck.pop())
        self.render(False)
        if aces:
            self.sitting[self.active] = True                 # one card on split aces, then done
            self.after(500, self.advance_hand)
        self.sync_actions()

    def end_hand(self):
        self.sitting[self.active] = True
        self.after(350, self.advance_hand)

    def advance_hand(self):
        """Move to the next hand that still has to be played (and deal its first card)."""
        if all(self.sitting):
            return self.all_hands_done()
        nxt = next((i for i in range(self.active + 1, len(self.hands)) if not self.sitting[i]), None)
        if nxt is None:
            return self.all_hands_done()
        self.active = nxt
        self.player, self.stake = self.hands[nxt], self.stakes[nxt]
        if len(self.hands[nxt]) == 1:
            self.hands[nxt].append(self.deck.pop())          # the second hand of a split gets dealt now
        self.render(False)
        if self.split_aces:
            self.sitting[nxt] = True                         # split aces get exactly one card
            return self.after(500, self.advance_hand)
        self.sync_actions()

    # ---- the dealer and the settlement
    def all_hands_done(self):
        self.playing = False
        for b in (self.hit_btn, self.stand_btn, self.split_btn, self.double_btn):
            b.setEnabled(False)
        self.render(True, flip_hole=True)
        if all(rules.bj_value(h) > 21 for h in self.hands):  # nothing left to beat: settle at once
            return self.settle_hands()
        self.after(800, self.dealer_step)

    def dealer_step(self):
        if rules.bj_value(self.dealer) < 17:
            self.dealer.append(self.deck.pop())
            self.render(True)
            self.after(800, self.dealer_step)
        else:
            self.settle_hands()

    def settle_hands(self):
        deltas, texts, tags, shorts = [], [], [], []
        for hand, stake in zip(self.hands, self.stakes):
            if rules.bj_value(hand) > 21:
                delta, text, tg = -stake, 'Bust! You lost.', ()
                short = 'bust'
            else:
                delta, _win, text, tg = rules.settle_blackjack(hand, self.dealer, stake)
                if self.ever_split and 'natural' in tg:
                    # a natural only pays 3:2 on the original, unsplit two-card hand
                    delta, text, tg = stake, 'You win! (split hands pay 1:1)', ()
                short = 'won' if delta > 0 else 'lost' if delta < 0 else 'push'
            deltas.append(delta)
            texts.append(text)
            shorts.append(short)
            tags.extend(tg)
        total = sum(deltas)
        win = True if total > 0 else False if total < 0 else None
        tags = tuple(dict.fromkeys(tags))
        if len(self.hands) == 1:
            text = texts[0]
        else:
            text = (f'{len(self.hands)} hands vs dealer {rules.bj_value(self.dealer)}: '
                    + ', '.join(f'hand {i + 1} {s} {"+" if d > 0 else ""}{d:,}'
                                for i, (s, d) in enumerate(zip(shorts, deltas))))
        if 'natural' in tags:                                # a natural blackjack deserves a flourish
            self.fx_flash('#f4c542', 45, 380)
            self.ring_on(self.player_row, 0.5, 0.5, color='#ffe9a3', r1=130, width=4, ms=440)
        if win is True:
            self.fx_flash('#f4c542', 45, 380)
            self.burst_on(self.player_row, 0.5, 0.5, n=24, colors=['#f4c542', '#ffe9a3', '#e8eaf0'],
                          speed=(2.0, 6.5), gravity=0.22, size=(3, 7), life=(34, 62))
        self.finish(total, win, text, tags)

    def render(self, reveal, flip_hole=False):
        fx = self.effects_on() and self.app.anim_factor() > 0
        d = self.dealer
        prev_p = getattr(self, '_n_player', 0)          # what was already on the table last time
        prev_d = getattr(self, '_n_dealer', 0)
        self.player_row.set_cards([(c[0], c[2]) for c in self.player])
        self.player_total.setText(f'Your hand: {rules.bj_value(self.player)}'
                                  + (f'   •   stake {self.stake:,} TL' if len(self.hands) > 1 else ''))
        if len(self.hands) > 1:
            self.you_lbl.setText(f'You  —  hand {self.active + 1} of {len(self.hands)}')
        else:
            self.you_lbl.setText('You')
        flip_w = None
        if reveal:
            if fx and flip_hole and len(d) > 1:
                # keep the hole card face down, then turn it over with a flip animation
                self.dealer_row.set_cards([(d[0][0], d[0][2])] + [None] * (len(d) - 1))
                flip_w = self.dealer_row.lay.itemAt(1).widget()
                if flip_w is not None:
                    fade_flip(flip_w, lambda: paint_card(flip_w, (d[1][0], d[1][2])))
            else:
                self.dealer_row.set_cards([(c[0], c[2]) for c in d])
            self.dealer_total.setText(f"Dealer's hand: {rules.bj_value(d)}")
        else:
            self.dealer_row.set_cards([(d[0][0], d[0][2])] + [None] * (len(d) - 1))
            self.dealer_total.setText(f"Dealer's visible card: {d[0][1]}")
        # purely visual: only a card that was just dealt floats up - cards already on
        # the table stay perfectly still instead of blinking on every action
        if fx:
            if prev_p == 0 and prev_d == 0:               # the opening deal
                self._fade_row(self.player_row)
                self._fade_row(self.dealer_row)
            else:
                if len(self.player) > prev_p:
                    self._fade_last(self.player_row)
                if len(d) > prev_d:
                    self._fade_last(self.dealer_row, skip=flip_w)
        self._n_player, self._n_dealer = len(self.player), len(d)

    @staticmethod
    def _fade_last(row, skip=None):
        if row.lay.count():
            w = row.lay.itemAt(row.lay.count() - 1).widget()
            if w is not None and w is not skip:
                fade_in(w, 240)

    @staticmethod
    def _fade_row(row, delay0=0):
        for i in range(row.lay.count()):
            w = row.lay.itemAt(i).widget()
            if w is not None:
                fade_in(w, 240, delay=delay0 + 70 * i)


class PokerGame(BaseGame):
    key, title = 'poker', 'Poker (5 Card Draw)'

    @staticmethod
    def rs(r):
        return rules.RANK_STR.get(r, str(r))

    def style_card(self, b, c):
        col = '#c62828' if c[1] in rules.RED else '#111111'
        b.setText(f'{self.rs(c[0])}\n{c[1]}')
        b.setStyleSheet(
            'QPushButton{background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #ffffff,stop:1 #eceff4);'
            f'color:{col};border:2px solid #cfcfcf;border-radius:10px;font-size:24px;font-weight:700;padding:0;}}'
            'QPushButton:checked{background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #fff6d0,stop:1 #ffe08a);'
            'border:3px solid #d4a017;}'
            f'QPushButton:disabled{{background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #ffffff,stop:1 #eceff4);'
            f'color:{col};border:2px solid #cfcfcf;}}')

    def build(self):
        self.deck = rules.new_deck_poker(self.rng)
        self.player = [self.deck.pop() for _ in range(5)]
        self.computer = [self.deck.pop() for _ in range(5)]
        self.lock(True)
        self.body.addWidget(centered('Computer', 'hint'))
        self.comp_row = CardRow()
        self.comp_row.set_cards([None] * 5)
        self.body.addWidget(self.comp_row)
        self.comp_name = centered('', 'prompt')
        self.body.addWidget(self.comp_name)
        self.body.addStretch()
        self.body.addWidget(centered('Your hand: click the cards you want to change  [1-5]', 'hint'))
        row = QHBoxLayout()
        row.setAlignment(AC)
        self.btns, self.tags = [], []
        for i, c in enumerate(self.player):
            col = QVBoxLayout()
            b = Button()
            b.setCheckable(True)
            b.setFixedSize(76, 108)
            self.style_card(b, c)
            b.toggled.connect(lambda _c, i=i: self.on_toggle(i))
            tag = centered('KEEP', 'hint')
            col.addWidget(b)
            col.addWidget(tag)
            row.addLayout(col)
            self.btns.append(b)
            self.tags.append(tag)
            self.bind(digit_key(i + 1), b)
        self.body.addLayout(row)
        self.you_name = centered('', 'prompt')
        self.body.addWidget(self.you_name)
        self.go = Button('Keep all cards  [Space]')
        self.go.setObjectName('primary')
        self.go.setMinimumHeight(48)
        self.go.clicked.connect(self.confirm)
        self.body.addWidget(self.go)
        self.bind(K.Key_Space, self.go)
        self.bind(K.Key_Return, self.go)
        self.bind(K.Key_Enter, self.go)

    def on_toggle(self, i):
        self.tags[i].setText('CHANGE' if self.btns[i].isChecked() else 'KEEP')
        n = sum(b.isChecked() for b in self.btns)
        self.go.setText('Keep all cards  [Space]' if n == 0 else f'Change {n} card{"s" if n > 1 else ""}  [Space]')

    def confirm(self):
        changed = [i for i, b in enumerate(self.btns) if b.isChecked()]
        for i in changed:
            self.player[i] = self.deck.pop()
        rules.computer_draw(self.computer, self.deck, self.rng)
        for i, b in enumerate(self.btns):
            b.setChecked(False)
            b.setEnabled(False)
            self.tags[i].setText('')
        self.go.setEnabled(False)
        fx_on = self.effects_on() and self.app.anim_factor() > 0
        for i, b in enumerate(self.btns):                # the kept cards stay; changed ones flip over
            if fx_on and i in changed:
                self.after(60 * i, lambda i=i, b=b: fade_flip(b, lambda: self.style_card(b, self.player[i])))
            else:
                self.style_card(b, self.player[i])
        self.comp_row.set_cards(self.computer)
        if fx_on:                                        # the computer's hand turns face up, one card at a time
            for i in range(self.comp_row.lay.count()):
                w = self.comp_row.lay.itemAt(i).widget()
                if w is not None:
                    fade_in(w, 260, delay=70 * i)
        pr, cr = rules.poker_hand_rank(self.player), rules.poker_hand_rank(self.computer)
        self.you_name.setText(f'You: {rules.POKER_NAMES[pr[0]]}')
        self.comp_name.setText(f'Computer: {rules.POKER_NAMES[cr[0]]}')
        if fx_on:                                        # the winning hand's name lights up
            win = self.you_name if pr[0] > cr[0] else (self.comp_name if cr[0] > pr[0] else None)
            if win is not None:
                self.after(700, lambda: (self.pulse(win, 'color:#ffe9a3; font-size:26px;', 320),
                                         self.ring_on(win, 0.5, 0.5, color='#ffe9a3', r1=110, width=3, ms=420)))
        self.after(900, lambda: self.finish_with(rules.settle_poker(pr, cr, self.bet)))


class LottoGame(BaseGame):
    key, title = 'tombala', 'Lotto'

    def build(self):
        self.chosen = set()
        self.body.addWidget(centered(f'Pick 6 numbers between 1 and {rules.LOTTO_POOL}', 'prompt'))
        grid = QGridLayout()
        grid.setSpacing(5)
        self.btns = {}
        for n in range(1, rules.LOTTO_POOL + 1):
            b = Button(str(n))
            b.setObjectName('num')
            b.setCheckable(True)
            b.setFixedSize(46, 38)
            b.toggled.connect(lambda checked, n=n: self.toggle(n, checked))
            grid.addWidget(b, (n - 1) // 10, (n - 1) % 10)
            self.btns[n] = b
        gw = QWidget()
        gw.setLayout(grid)
        self.body.addWidget(gw, 0, AC)
        self.counter = centered('Selected: 0 / 6', 'hint')
        self.body.addWidget(self.counter)
        row = QHBoxLayout()
        self.quick_btn = Button('Quick pick  [Q]')
        self.clear_btn = Button('Clear  [C]')
        self.draw_btn = Button('Draw!  [Space]')
        self.draw_btn.setObjectName('primary')
        self.draw_btn.setEnabled(False)
        self.quick_btn.clicked.connect(self.quick_pick)
        self.clear_btn.clicked.connect(self.clear)
        self.draw_btn.clicked.connect(self.draw)
        for b in (self.quick_btn, self.clear_btn, self.draw_btn):
            b.setMinimumHeight(42)
            row.addWidget(b)
        self.body.addLayout(row)
        self.balls = QHBoxLayout()
        self.balls.setAlignment(AC)
        self.body.addLayout(self.balls)
        self.bind(K.Key_Q, self.quick_btn)
        self.bind(K.Key_C, self.clear_btn)
        self.bind(K.Key_Space, self.draw_btn)
        self.bind(K.Key_Return, self.draw_btn)
        self.bind(K.Key_Enter, self.draw_btn)

    def toggle(self, n, checked):
        if checked:
            if len(self.chosen) >= 6:
                self.btns[n].blockSignals(True)
                self.btns[n].setChecked(False)
                self.btns[n].blockSignals(False)
                return
            self.chosen.add(n)
        else:
            self.chosen.discard(n)
        self.counter.setText(f'Selected: {len(self.chosen)} / 6')
        self.draw_btn.setEnabled(len(self.chosen) == 6)

    def clear(self):
        for n in list(self.chosen):
            self.btns[n].setChecked(False)

    def quick_pick(self):
        self.clear()
        for n in self.rng.sample(range(1, rules.LOTTO_POOL + 1), 6):
            self.btns[n].setChecked(True)

    def draw(self):
        self.lock(True)
        for b in (self.quick_btn, self.clear_btn, self.draw_btn):
            b.setEnabled(False)
        for n, b in self.btns.items():
            b.setEnabled(False)
            if n in self.chosen:
                paint(b, '#d4a017', '#1a1400', '#f4c542')
        self.drawn = rules.lotto_draw(self.rng)
        self.matches = 0
        self.shown = 0

        def reveal_next():                     # every ball is revealed exactly once
            n = self.drawn[self.shown]
            self.shown += 1
            hit = n in self.chosen
            if hit:
                self.matches += 1
                paint(self.btns[n], '#4cc38a', '#06281a', '#4cc38a')
            else:
                paint(self.btns[n], '#2a3348', '#e8eaf0', '#ff6b6b')
            ball = QLabel(str(n))
            ball.setFixedSize(44, 44)
            ball.setAlignment(AC)
            ball.setStyleSheet(
                f"background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 {('#7ee0ad' if hit else '#4a5672')},"
                f"stop:1 {('#3aa76d' if hit else '#2f3a52')});"
                f"color:{'#06281a' if hit else '#e8eaf0'};"
                'border:2px solid '
                f"{'#4cc38a' if hit else '#5a688a'};"
                'border-radius:22px;font-size:16px;font-weight:800;')
            self.balls.addWidget(ball)
            ball.show()
            if self.app.settings.effects and self.app.anim_factor() > 0:
                # the ball drops in and bounces, hits flash gold
                fade_in(ball, 220)
                self.burst_on(ball, 0.5, 0.5, n=8,
                              colors=['#ffe9a3', '#4cc38a'] if hit else ['#8d97a8', '#c8cfdb'],
                              speed=(0.8, 2.4), gravity=0.35, size=(2, 5))
                if hit:
                    self.pulse(self.btns[n], 'background:#ffe9a3; color:#111; border-radius:10px;', 320)
                    self.ring_on(self.btns[n], 0.5, 0.5, color='#4cc38a', r1=60, width=3, ms=340)
            self.counter.setText(f'Matched numbers: {self.matches}')

        def done():
            while self.shown < 6:
                reveal_next()
            if self.matches >= 4 and self.effects_on():   # a rare haul deserves confetti
                self.fx_flash('#f4c542', 40, 400)
                for i in range(self.balls.count()):
                    w = self.balls.itemAt(i).widget()
                    if w is not None:
                        self.burst_on(w, 0.5, 0.4, n=10, colors=['#f4c542', '#ffe9a3', '#4cc38a'],
                                      speed=(1.2, 3.6), gravity=0.3, size=(3, 6))
            self.finish_with(rules.settle_lotto(self.matches, self.bet))
        reveal_next()
        self.animate(6, 550, lambda n: reveal_next(), done)


class BaccaratGame(BaseGame):
    key, title = 'baccarat', 'Baccarat'

    def build(self):
        self.deck = rules.new_deck_bac(self.rng)
        self.body.addWidget(centered('Banker', 'hint'))
        self.banker_row = CardRow()
        self.banker_row.set_cards([None, None])
        self.body.addWidget(self.banker_row)
        self.banker_total = centered('', 'prompt')
        self.body.addWidget(self.banker_total)
        self.body.addStretch()
        self.body.addWidget(centered('Player', 'hint'))
        self.player_row = CardRow()
        self.player_row.set_cards([None, None])
        self.body.addWidget(self.player_row)
        self.player_total = centered('', 'prompt')
        self.body.addWidget(self.player_total)
        self.body.addWidget(centered("Who will win? Pays 1.9×. A tie returns your bet.", 'prompt'))
        row = QHBoxLayout()
        self.btns = []
        for who, label, key in (('player', 'Bet on Player  [P]', K.Key_P), ('banker', 'Bet on Banker  [B]', K.Key_B)):
            b = Button(label)
            b.setObjectName('primary')
            b.setMinimumHeight(48)
            b.clicked.connect(lambda _=False, w=who: self.pick(w))
            row.addWidget(b)
            self.btns.append(b)
            self.bind(key, b)
        self.body.addLayout(row)

    def pick(self, who):
        for b in self.btns:
            b.setEnabled(False)
        self.lock(True)
        p = [self.deck.pop(), self.deck.pop()]
        b = [self.deck.pop(), self.deck.pop()]
        fx_on = self.effects_on() and self.app.anim_factor() > 0

        def show(k):  # k cards revealed in the order P, B, P, B
            pc = [p[0] if k >= 1 else None, p[1] if k >= 3 else None]
            bc = [b[0] if k >= 2 else None, b[1] if k >= 4 else None]
            self.player_row.set_cards([(c[0], c[2]) if c else None for c in pc])
            self.banker_row.set_cards([(c[0], c[2]) if c else None for c in bc])
            if fx_on:                       # each freshly turned card fades up like a real deal
                for row, cards, off in ((self.player_row, pc, 1), (self.banker_row, bc, 2)):
                    for j, c in enumerate(cards):
                        w = row.lay.itemAt(j).widget() if j < row.lay.count() else None
                        if c and w is not None and k == j * 2 + off:   # P1,B1,P2,B2 order
                            fade_in(w, 240)

        def done():
            show(4)
            ps, bs = rules.bac_total(p), rules.bac_total(b)
            self.player_total.setText(f'Player total: {ps}')
            self.banker_total.setText(f'Banker total: {bs}')
            if fx_on:
                for total, row in ((ps, self.player_row), (bs, self.banker_row)):
                    self.ring_on(row, 0.5, 0.5, color='#ffe9a3' if total > 0 else '#8d97a8',
                                 r1=110, width=3, ms=400)
            self.finish_with(rules.settle_baccarat(who, ps, bs, self.bet))
        show(1)
        self.animate(4, 600, lambda n: show(n + 1), done)


class HorseTrack(QWidget):
    """A dirt track where five horses gallop side by side. Purely visual: the game owns the
    positions (0..1 along the track) and the winner; this only draws them running."""

    COATS = ['#7a4a2b', '#3c3f4d', '#8a6a3b', '#5b4433', '#6e5a44']   # horse coats
    SILKS = ['#e5484d', '#4c9be8', '#4cc38a', '#e0a526', '#b06ee0']   # jockey silks

    def __init__(self):
        super().__init__()
        self.setMinimumHeight(320)
        self.pos = [0.0] * 5            # 0..1 along the track
        self.speed = [0.0] * 5          # how hard each one is running (for strides and dust)
        self.phase = [VRNG.uniform(0, 2 * math.pi) for _ in range(5)]
        self.winner = None
        self.racing = False
        self.gate_up = 0.0              # start gate height (0 = down)
        self.dust = []                  # [x, y, r, life]
        self.crowd = [(VRNG.uniform(0, 1), VRNG.randint(0, 2), VRNG.choice(
            ['#e8eaf0', '#f4c542', '#4cc38a', '#ff6b6b', '#6c8cff', '#b06ee0'])) for _ in range(150)]
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)

    # ---- driving (the game sets positions; the timer only animates the strides)
    def set_positions(self, pos):
        pos = list(pos)
        self.speed = [max(0.0, p - o) * 7 for p, o in zip(pos, self.pos)]
        self.pos = pos
        self.update()

    def start_running(self):
        self.racing = True
        self.timer.start(16)

    def stop_running(self):
        self.racing = False
        self.timer.stop()

    def _tick(self):
        for i in range(5):
            self.phase[i] += 0.5 + self.speed[i] * 0.45
            if self.racing and VRNG.random() < 0.05 + self.speed[i] * 0.12:
                self.dust.append([96 + self.pos[i] * max(1, self.width() - 190), VRNG.uniform(200, 250),
                                  VRNG.uniform(3, 8), 1.0])
        for d in self.dust:
            d[2] += 0.8
            d[3] -= 0.05
        self.dust = [d for d in self.dust if d[3] > 0]
        if self.gate_up < 1.0:
            self.gate_up = min(1.0, self.gate_up + 0.08)
        self.update()

    # ---- drawing
    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        # sky and grandstand
        sky = QLinearGradient(0, 0, 0, 74)
        sky.setColorAt(0, QColor('#101728'))
        sky.setColorAt(1, QColor('#1b2540'))
        p.fillRect(QRectF(0, 0, w, 74), sky)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor('#232b3d'))
        p.drawRect(QRectF(0, 34, w, 40))
        for cx, row, col in self.crowd:                    # a bobbing crowd of dots
            bob = 2.0 * abs(math.sin(self.phase[0] * 0.15 + cx * 30))
            p.setBrush(QColor(col))
            p.drawEllipse(QPointF(cx * w, 44 + row * 9 - bob), 2.4, 2.4)
        p.setPen(QPen(QColor('#d4a017'), 3))
        p.drawLine(QPointF(0, 74), QPointF(w, 74))
        # turf and dirt
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor('#16351f'))
        p.drawRect(QRectF(0, 75, w, h - 75))
        dirt = QLinearGradient(0, 96, 0, h)
        dirt.setColorAt(0, QColor('#8a6a45'))
        dirt.setColorAt(1, QColor('#5d452c'))
        p.setBrush(dirt)
        p.drawRect(QRectF(0, 96, w, h - 96))
        lane_top, lane_h = 100, (h - 104) / 5
        p.setPen(QPen(QColor(255, 255, 255, 26), 1, Qt.PenStyle.DashLine))
        for i in range(1, 5):
            y = lane_top + i * lane_h
            p.drawLine(QPointF(0, y), QPointF(w, y))
        x0, x1 = 96, w - 74                                 # gate to finish line
        # finish line + winning post
        p.setBrush(QColor('#f4c542'))
        p.drawRect(QRectF(x1 - 4, 90, 8, h - 94))
        for r in range(int((h - 100) // 12)):
            for c in range(2):
                p.setBrush(QColor('#111111') if (r + c) % 2 else QColor('#e8eaf0'))
                p.drawRect(QRectF(x1 + 6 + c * 9, 100 + r * 12, 9, 12))
        # the start gate (lifts when the race begins)
        if self.gate_up < 1.0:
            p.setBrush(QColor(120, 130, 150, 200))
            p.setPen(QPen(QColor('#c9d1e0'), 2))
            p.drawRect(QRectF(x0 - 14, lane_top + (1 - self.gate_up) * 0 - 4, 10, lane_h * 5 + 8))
        for i in range(5):
            y = lane_top + lane_h * (i + 0.5)
            p.setBrush(QColor('#0e1119'))
            p.setPen(QPen(QColor('#39415a'), 1))
            p.drawRoundedRect(QRectF(8, y - 15, 74, 30), 8, 8)
            p.setPen(QColor(self.SILKS[i]))
            f = p.font()
            f.setBold(True)
            f.setPointSize(15)
            p.setFont(f)
            p.drawText(QRectF(8, y - 15, 74, 30), AC, f'{i + 1}  {rules.RACE_NAMES[i]}')
        for d in self.dust:                                 # kicked-up dirt
            c = QColor('#c9b391')
            c.setAlpha(int(150 * d[3]))
            p.setBrush(c)
            p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(QPointF(d[0], d[1]), d[2], d[2] * 0.7)
        for i in range(5):                                  # the horses, back to front
            x = x0 + self.pos[i] * (x1 - x0)
            y = lane_top + lane_h * (i + 0.5) + lane_h * 0.30
            self._draw_horse(p, x, y, self.phase[i], self.speed[i], i,
                             dim=(self.winner is not None and self.winner != i))

    def _draw_horse(self, p, x, y, phase, speed, i, dim=False):
        """One galloping horse with its jockey, hooves at (x, y)."""
        p.save()
        p.translate(x, y)
        if dim:
            p.setOpacity(0.45)
        coat, silk = QColor(self.COATS[i]), QColor(self.SILKS[i])
        dark = coat.darker(140)
        light = coat.lighter(125)
        bob = 3.0 * abs(math.sin(phase))                     # the body bounces with the gallop
        stretch = math.sin(phase * 0.5)                      # fore/hind reach, a rocking gallop
        p.translate(0, -bob)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(0, 0, 0, 70))
        p.drawEllipse(QPointF(2, bob), 28, 5)                # shadow on the dirt

        def leg(hx, hy, off, near):
            """One leg: upper (thick), lower (thin) and a dark hoof. `off` staggers the stride."""
            sw = math.sin(phase + off)
            fold = 4 * max(0.0, math.sin(phase + off + 1.1))   # the leg folds up mid-stride
            knee = QPointF(hx + sw * 8, hy + 13 - fold)
            hoof = QPointF(hx + sw * 14 + stretch * 3, 1 - fold * 0.8)
            p.setPen(QPen(dark if not near else coat, 6 if near else 5,
                          Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            p.drawLine(QPointF(hx, hy), knee)
            p.setPen(QPen(dark if not near else coat, 4 if near else 3,
                          Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            p.drawLine(knee, hoof)
            p.setBrush(QColor('#191410'))
            p.drawEllipse(hoof, 2.5, 2.0)

        # far pair first, so the body covers their tops
        leg(-15, -26, math.pi * 0.2 + stretch * 0.3, False)   # far hind
        leg(15, -26, math.pi * 1.0 - stretch * 0.3, False)    # far fore
        # barrel of the body + rump and chest bulges
        p.setPen(QPen(dark, 2))
        p.setBrush(coat)
        p.drawEllipse(QRectF(-24, -46, 48, 26))
        p.drawEllipse(QRectF(-26, -44, 22, 22))               # rump
        p.drawEllipse(QRectF(6, -44, 22, 22))                 # chest
        # neck: a tapered polygon from the shoulder up to the head
        p.drawPolygon(QPolygonF([QPointF(10, -44), QPointF(26, -64), QPointF(35, -60), QPointF(21, -38)]))
        # head: rounded wedge pointing down the stretch, with muzzle, mane and ear
        p.save()
        p.translate(33, -62)
        p.rotate(28)
        p.drawRoundedRect(QRectF(-4, -7, 22, 14), 7, 7)
        p.restore()
        p.setBrush(QColor('#241a12'))
        p.drawEllipse(QPointF(45, -52), 3.5, 3)               # muzzle
        p.setBrush(dark)
        p.drawPolygon(QPolygonF([QPointF(28, -68), QPointF(31, -76), QPointF(34, -67)]))   # ear
        p.setBrush(QColor('#101010'))
        p.drawEllipse(QPointF(35, -64), 1.6, 1.6)             # eye
        p.setPen(QPen(dark, 4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        wag = 4 * math.sin(phase * 0.7)
        p.drawLine(QPointF(-24, -42), QPointF(-42 - speed * 5, -50 + wag))   # streaming tail
        # jockey in the horse's silks, folded low over the withers
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(silk)
        p.drawRoundedRect(QRectF(-10, -60, 22, 15), 7, 7)     # crouched torso
        p.setBrush(silk.darker(120))
        p.drawRoundedRect(QRectF(8, -54, 14, 7), 4, 4)        # arms reaching to the neck
        p.setBrush(QColor('#e8c39e'))
        p.drawEllipse(QPointF(15, -63), 6, 6)                 # face
        p.setBrush(silk.lighter(145))
        p.drawEllipse(QPointF(14, -66), 7, 5)                 # helmet
        p.setBrush(QColor('#1d1d22'))
        p.drawEllipse(QPointF(-8, -46), 3.5, 3)               # boot in the stirrup
        # near legs last, on top of the body
        leg(-13, -26, math.pi * 1.2 - stretch * 0.3, True)    # near hind
        leg(17, -26, math.pi * 0.4 + stretch * 0.3, True)     # near fore
        if self.winner == i:                                 # a gold halo for the winner
            p.setPen(QPen(QColor(244, 197, 66, 150), 3))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawEllipse(QPointF(6, -42), 48, 42)
        p.restore()


class RaceGame(BaseGame):
    key, title = 'race', 'Race Betting'
    COLORS = HorseTrack.SILKS

    def build(self):
        self.body.addWidget(centered('Pick the horse you think will win. Pays 4×.  [1-5]', 'prompt'))
        self.track = HorseTrack()
        self.body.addWidget(self.track, 1)
        row = QHBoxLayout()
        self.btns = []
        for i, name in enumerate(rules.RACE_NAMES):
            b = Button(f'Bet on {i + 1} – {name}')
            b.clicked.connect(lambda _=False, i=i: self.go(i))
            row.addWidget(b)
            self.btns.append(b)
            self.bind(digit_key(i + 1), b)
        self.body.addLayout(row)

    def go(self, pick):
        for b in self.btns:
            b.setEnabled(False)
        self.lock(True)
        winner = self.rng.randint(0, 4)                      # the result, decided before the race starts
        targets = [VRNG.uniform(0.80, 0.96) for _ in range(5)]
        targets[winner] = 1.0
        cur = [0.0] * 5
        T = 40
        self.track.start_running()

        def tick(n):
            for i in range(5):
                v = targets[i] * n / T + VRNG.uniform(-0.05, 0.05) * (1 - n / T)
                cur[i] = max(cur[i], min(v, targets[i]))
            self.track.set_positions(cur)

        def done():
            self.track.stop_running()
            self.track.winner = winner
            self.track.set_positions(targets)
            pt = self.track.mapTo(self.felt, QPoint(self.track.width() - 60, 60))   # mapTo returns a QPoint
            self.burst_at(pt.x(), pt.y(), n=26, colors=['#f4c542', '#ffe9a3', self.track.SILKS[winner]],
                          speed=(2.0, 7.0), gravity=0.3, size=(3, 7), life=(30, 60))
            self.finish_with(rules.settle_race(pick, winner, self.bet))
        self.animate(T, 85, tick, done)
