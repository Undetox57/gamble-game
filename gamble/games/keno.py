"""Keno: pick ten numbers, ten balls are drawn from forty, every hit pays.

The maths lives in rules.keno_* (exact hypergeometric RTP, ~90%), this file is only the table."""
from PyQt6.QtWidgets import QGridLayout, QLabel, QWidget

from .. import rules
from ..fx import fade_in
from ..widgets import AC, Button, centered, paint
from .base import BaseGame, K

BALL_CSS = ("background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 {top},"
            "stop:1 {bottom});color:{fg};border:2px solid {edge};border-radius:20px;"
            "font-size:15px;font-weight:800;")


class KenoGame(BaseGame):
    key, title = 'keno', 'Keno'

    def build(self):
        self.chosen = set()
        self.body.addWidget(centered(f'Pick {rules.KENO_PICK} numbers out of {rules.KENO_POOL}. '
                                     f'The draw takes {rules.KENO_DRAW}.', 'prompt'))
        pay = '   '.join(f'{h} hit = {m:g}×' for h, m in sorted(rules.KENO_PAYOUT.items()))
        self.body.addWidget(centered(f'Payouts:  {pay}', 'hint'))
        grid = QGridLayout()
        grid.setSpacing(5)
        self.btns = {}
        for n in range(1, rules.KENO_POOL + 1):
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
        self.counter = centered(f'Selected: 0 / {rules.KENO_PICK}', 'hint')
        self.body.addWidget(self.counter)
        row = QGridLayout()
        self.quick_btn = Button('Quick pick  [Q]')
        self.clear_btn = Button('Clear  [C]')
        self.draw_btn = Button('Draw!  [Space]')
        self.draw_btn.setObjectName('primary')
        self.draw_btn.setEnabled(False)
        self.quick_btn.clicked.connect(self.quick_pick)
        self.clear_btn.clicked.connect(self.clear)
        self.draw_btn.clicked.connect(self.draw)
        for i, b in enumerate((self.quick_btn, self.clear_btn, self.draw_btn)):
            b.setMinimumHeight(42)
            row.addWidget(b, 0, i)
        row.setColumnStretch(0, 1)
        row.setColumnStretch(1, 1)
        row.setColumnStretch(2, 2)
        self.body.addLayout(row)
        self.balls = QGridLayout()
        self.balls.setHorizontalSpacing(8)
        self.balls.setVerticalSpacing(8)
        self.balls.setAlignment(AC)
        self.body.addLayout(self.balls)
        self.bind(K.Key_Q, self.quick_btn)
        self.bind(K.Key_C, self.clear_btn)
        self.bind(K.Key_Space, self.draw_btn)
        self.bind(K.Key_Return, self.draw_btn)
        self.bind(K.Key_Enter, self.draw_btn)

    def toggle(self, n, checked):
        if checked:
            if len(self.chosen) >= rules.KENO_PICK:
                self.btns[n].blockSignals(True)
                self.btns[n].setChecked(False)
                self.btns[n].blockSignals(False)
                return
            self.chosen.add(n)
        else:
            self.chosen.discard(n)
        self.counter.setText(f'Selected: {len(self.chosen)} / {rules.KENO_PICK}')
        self.draw_btn.setEnabled(len(self.chosen) == rules.KENO_PICK)

    def clear(self):
        for n in list(self.chosen):
            self.btns[n].setChecked(False)

    def quick_pick(self):
        self.clear()
        for n in self.rng.sample(range(1, rules.KENO_POOL + 1), rules.KENO_PICK):
            self.btns[n].setChecked(True)

    def draw(self):
        self.lock(True)
        for b in (self.quick_btn, self.clear_btn, self.draw_btn):
            b.setEnabled(False)
        for n, b in self.btns.items():
            b.setEnabled(False)
            if n in self.chosen:
                paint(b, '#d4a017', '#1a1400', '#f4c542')
        self.drawn = rules.keno_draw(self.rng)
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
            ball.setFixedSize(40, 40)
            ball.setAlignment(AC)
            ball.setStyleSheet(BALL_CSS.format(top='#7ee0ad' if hit else '#4a5672',
                                                bottom='#3aa76d' if hit else '#2f3a52',
                                                fg='#06281a' if hit else '#e8eaf0',
                                                edge='#4cc38a' if hit else '#5a688a'))
            self.balls.addWidget(ball, (self.shown - 1) // 5, (self.shown - 1) % 5)
            ball.show()
            if self.app.settings.effects and self.app.anim_factor() > 0:
                fade_in(ball, 220)
                self.burst_on(ball, 0.5, 0.5, n=8,
                              colors=['#ffe9a3', '#4cc38a'] if hit else ['#8d97a8', '#c8cfdb'],
                              speed=(0.8, 2.4), gravity=0.35, size=(2, 5))
                if hit:
                    self.pulse(self.btns[n], 'background:#ffe9a3; color:#111; border-radius:10px;', 320)
                    self.ring_on(self.btns[n], 0.5, 0.5, color='#4cc38a', r1=60, width=3, ms=340)
            self.counter.setText(f'Matched: {self.matches} of {self.shown} drawn')

        def done():
            while self.shown < rules.KENO_DRAW:
                reveal_next()
            if self.matches >= 6 and self.effects_on():   # a rare haul deserves confetti
                self.fx_flash('#f4c542', 40, 400)
                for i in range(self.balls.count()):
                    w = self.balls.itemAt(i).widget()
                    if w is not None:
                        self.burst_on(w, 0.5, 0.4, n=10, colors=['#f4c542', '#ffe9a3', '#4cc38a'],
                                      speed=(1.2, 3.6), gravity=0.3, size=(3, 6))
            self.finish_with(rules.settle_keno(self.matches, self.bet))

        reveal_next()
        self.animate(rules.KENO_DRAW, 380, lambda n: reveal_next(), done)
