"""Hi-Lo: guess whether the next card is higher or lower. Every win multiplies your stake."""
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QWidget

from .. import rules
from ..fx import VRNG
from ..widgets import AC, Button, centered, make_card, paint_card
from .base import BaseGame, K

BIG = (116, 164)                        # the card on show is bigger than the deck used elsewhere


class HiLoGame(BaseGame):
    key, title = 'hilo', 'Hi-Lo'

    def build(self):
        self.deck = rules.new_deck_hilo(self.rng)
        self.card = self.deck.pop()
        self.probs, self.mult = [], 1.0
        self.done, self.busy = False, False

        self.body.addStretch()
        self.card_lbl = make_card(self.card, BIG)
        self.body.addWidget(self.card_lbl, 0, AC)
        self.ask = centered('', 'prompt')
        self.body.addWidget(self.ask)
        row = QHBoxLayout()
        self.high_btn = Button('Higher  [H]')
        self.low_btn = Button('Lower  [L]')
        for b in (self.high_btn, self.low_btn):
            b.setMinimumHeight(50)
            row.addWidget(b)
        self.high_btn.clicked.connect(lambda: self.guess(True))
        self.low_btn.clicked.connect(lambda: self.guess(False))
        self.body.addLayout(row)
        # what is still in the deck: one box per rank with the number of copies left,
        # coloured by which side it would settle - the strategy is visible instead of guessed
        self.deck_panel = QWidget()
        dl = QHBoxLayout(self.deck_panel)
        dl.setContentsMargins(0, 0, 0, 0)
        dl.setSpacing(4)
        self.deck_cells = []
        for rank in rules.HILO_ORDER:
            cell = QLabel(rank)
            cell.setFixedSize(40, 44)
            cell.setAlignment(AC)
            dl.addWidget(cell)
            self.deck_cells.append(cell)
        self.body.addWidget(self.deck_panel, 0, AC)
        self.deck_legend = centered(
            '<span style="color:#4cc38a">■</span> beats this card (higher wins)     '
            '<span style="color:#6c8cff">■</span> below it (lower wins)     '
            '<span style="color:#9fb8ac">■</span> tie, re-dealt', 'hint')
        self.body.addWidget(self.deck_legend)
        self.mult_lbl = QLabel('1×')
        self.mult_lbl.setObjectName('bigMoney')
        self.mult_lbl.setAlignment(AC)
        self.body.addWidget(self.mult_lbl)
        self.hint = centered('', 'hint')
        self.body.addWidget(self.hint)
        self.cash_btn = Button('CASH OUT  [Space]')
        self.cash_btn.setObjectName('primary')
        self.cash_btn.setMinimumHeight(50)
        self.cash_btn.setEnabled(False)
        self.cash_btn.clicked.connect(self.cash_out)
        self.body.addWidget(self.cash_btn)
        self.body.addStretch()

        self.bind(K.Key_H, self.high_btn)
        self.bind(K.Key_L, self.low_btn)
        self.bind(K.Key_Space, self.space_action)            # ahead of BaseGame's "play again"
        self.refresh()

    # ---- display
    def refresh(self):
        """Redraw the buttons: each one shows what your multiplier becomes if that guess wins."""
        current, playable = self.card[0], not self.done and bool(self.deck)
        for b, higher, key in ((self.high_btn, True, 'H'), (self.low_btn, False, 'L')):
            name = 'Higher' if higher else 'Lower'
            p = rules.hilo_prob(self.deck, current, higher) if playable else 0.0
            b.setEnabled(playable and p > 0 and not self.busy)
            b.setText(f'{name}  [{key}]'
                      + (f'   → {rules.hilo_multiplier(self.probs + [p], edge=self.edge):g}×' if p > 0 else ''))
        self.mult_lbl.setText(f'{self.mult:g}×')
        self.paint_deck()
        self.ask.setText(f'Higher or lower than {self.card[0]}{self.card[1]}?   '
                         f'({len(self.deck)} cards left)')
        if self.done or self.busy:
            self.cash_btn.setEnabled(False)
            self.hint.setText('Dealing...' if self.busy else '')
            return
        self.cash_btn.setEnabled(bool(self.probs))
        win = int(self.bet * self.mult) - self.bet
        self.cash_btn.setText(f'CASH OUT  [Space]   {"+" if win > 0 else ""}{win:,} TL' if self.probs
                              else 'CASH OUT  [Space]')
        if not self.deck:
            self.hint.setText('The deck has run dry - take your winnings.')
        elif self.probs:
            self.hint.setText(f'{len(self.probs)} in a row. Each button shows what it would pay out.')
        else:
            self.hint.setText('Pick a side - each button shows what a win pays. A 1x button is a safe '
                              'step forward with nothing to gain yet.')

    def paint_deck(self):
        """One box per rank: how many copies are left, coloured by the side it would settle."""
        counts = {}
        for label, _suit in self.deck:
            counts[label] = counts.get(label, 0) + 1
        cur = rules.HILO_ORDER.index(self.card[0])
        for i, (rank, cell) in enumerate(zip(rules.HILO_ORDER, self.deck_cells)):
            n = counts.get(rank, 0)
            if i == cur:                                   # ties are re-dealt: settles neither side
                bg, fg = ('#4a5266', '#e8eaf0') if n else ('#242a38', '#5f6779')
            elif i > cur:
                bg, fg = ('#1f8f5a', '#eafff4') if n else ('#17301f', '#54705f')
            else:
                bg, fg = ('#2f4d8f', '#eaf0ff') if n else ('#1a2035', '#565f7d')
            cell.setText(f'{rank}\n{n}')
            cell.setStyleSheet(f'background:{bg};color:{fg};border:2px solid {bg};'
                               'border-radius:8px;font-size:13px;font-weight:800;')

    def space_action(self):
        if self.done:                                        # BaseGame's bindings sit behind ours
            if self.again_btn.isVisible():
                self.again_btn.click()
        elif not self.busy and self.probs:
            self.cash_out()

    # ---- the round
    def guess(self, higher):
        if self.done or self.busy or not self.deck:
            return
        current = self.card
        p = rules.hilo_prob(self.deck, current[0], higher)
        if p <= 0:                                           # that side has nothing left to deal
            return
        nxt = rules.hilo_draw(self.deck, current[0])
        if nxt is None:                                      # only ties were left: nothing to bet on
            self.refresh()
            return
        self.busy = True
        if not self.in_progress:
            self.lock(True)
        self.refresh()

        def tick(_n):
            paint_card(self.card_lbl, (VRNG.choice(rules.HILO_ORDER), VRNG.choice(rules.SUITS)), BIG)

        def done():
            paint_card(self.card_lbl, nxt, BIG)
            self.card, self.busy = nxt, False
            if rules.hilo_beats(nxt, current) == higher:
                self.probs.append(p)
                self.mult = rules.hilo_multiplier(self.probs, edge=self.edge)
                self.pulse(self.mult_lbl, 'color:#ffe9a3; font-size:36px;', 280)   # the multiplier lights up
                self.burst_on(self.card_lbl, 0.5, 0.4, n=10, colors=['#4cc38a', '#a7f3cf'],
                              speed=(1.0, 3.0), gravity=0.18, size=(2, 5))
            else:
                self.fx_flash('#ff6b6b', 34, 280)
                self.done = True
                self.finish_with(rules.settle_hilo(
                    None, self.bet, f'You guessed {"higher" if higher else "lower"}, '
                                    f'but the card was {nxt[0]}{nxt[1]}', steps=len(self.probs)))
            self.refresh()
        self.animate(10, 70, tick, done)

    def cash_out(self):
        if self.done or self.busy or not self.probs:
            return
        self.done = True
        self.burst_on(self.cash_btn, 0.5, 0.4, n=20, colors=['#f4c542', '#ffe9a3', '#4cc38a'],
                      speed=(1.6, 5.0), gravity=0.25, size=(3, 6))
        self.finish_with(rules.settle_hilo(self.mult, self.bet, steps=len(self.probs)))
        self.refresh()
