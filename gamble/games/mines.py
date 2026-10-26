"""Mines: uncover safe cells to grow the multiplier, and cash out before you step on a mine."""
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QButtonGroup, QCheckBox, QDoubleSpinBox, QGridLayout, QHBoxLayout, QLabel, QWidget

from .. import rules
from ..fx import VRNG
from ..widgets import AC, Button, centered
from .base import BaseGame, K, digit_key

SIDE = 5                                    # the board is SIDE x SIDE cells


def tile_style(state, cursor=False):
    """state = 'hidden' | 'safe' | 'mine'."""
    if state == 'safe':
        top, bot, edge, fg = '#5ad39b', '#1f8f5a', '#a7f3cf', '#06301d'
    elif state == 'mine':
        top, bot, edge, fg = '#ff8a8a', '#b3261e', '#ffd0d0', '#2a0000'
    else:
        top, bot, edge, fg = '#37456a', '#2a3348', '#4d5a7d', '#9fb8ac'
    return ('QPushButton, QPushButton:disabled {background:qlineargradient(x1:0,y1:0,x2:0,y2:1,'
            'stop:0 %s,stop:1 %s);color:%s;border:3px solid %s;border-radius:9px;'
            'font-size:26px;font-weight:700;}'
            'QPushButton:hover {border-color:#f4c542;}') % (
        top, bot, fg, '#f4c542' if cursor else edge)


class MinesGame(BaseGame):
    key, title = 'mines', 'Mines'

    def build(self):
        self.risk = 'medium'
        self.mines = set()
        self.picks, self.mult = 0, 1.0
        self.done = False
        self.cursor = 0
        self.tiles = ['hidden'] * (SIDE * SIDE)

        row = QHBoxLayout()
        self.risk_group = QButtonGroup(self)
        self.risk_btns = {}
        for r, label, key in (('low', 'Low  [L]', K.Key_L), ('medium', 'Medium  [M]', K.Key_M),
                              ('high', 'High  [H]', K.Key_H)):
            b = Button(label)
            b.setCheckable(True)
            b.setMinimumHeight(40)
            b.setChecked(r == 'medium')
            b.clicked.connect(lambda _=False, r=r: self.set_risk(r))
            self.risk_group.addButton(b)
            self.risk_btns[r] = b
            row.addWidget(b)
            self.bind(key, b)
        self.body.addLayout(row)

        grid = QGridLayout()
        grid.setSpacing(7)
        self.cells = []
        for i in range(SIDE * SIDE):
            b = Button('')
            b.setFixedSize(76, 76)
            b.setStyleSheet(tile_style('hidden', cursor=(i == 0)))
            b.clicked.connect(lambda _=False, i=i: self.pick(i))
            grid.addWidget(b, i // SIDE, i % SIDE)
            self.cells.append(b)
        wrap = QWidget()
        wrap.setLayout(grid)
        self.body.addWidget(wrap, 0, AC)

        self.mult_lbl = QLabel('1×')
        self.mult_lbl.setObjectName('bigMoney')
        self.mult_lbl.setAlignment(AC)
        self.body.addWidget(self.mult_lbl)
        self.info = centered('', 'prompt')
        self.body.addWidget(self.info)
        auto = QHBoxLayout()
        auto.addStretch()
        self.auto_chk = QCheckBox('Auto cash out at')
        self.auto_spin = QDoubleSpinBox()
        self.auto_spin.setRange(1.01, 1000.0)
        self.auto_spin.setDecimals(2)
        self.auto_spin.setSingleStep(0.25)
        self.auto_spin.setValue(2.0)
        self.auto_spin.setSuffix('×')
        auto.addWidget(self.auto_chk)
        auto.addWidget(self.auto_spin)
        auto.addStretch()
        self.body.addLayout(auto)
        self.cash_btn = Button('CASH OUT  [Space]')
        self.cash_btn.setObjectName('primary')
        self.cash_btn.setMinimumHeight(50)
        self.cash_btn.setEnabled(False)
        self.cash_btn.clicked.connect(self.cash_out)
        self.body.addWidget(self.cash_btn)

        self.bind(K.Key_Up, lambda: self.move(0, -1))
        self.bind(K.Key_Down, lambda: self.move(0, 1))
        self.bind(K.Key_Left, lambda: self.move(-1, 0))
        self.bind(K.Key_Right, lambda: self.move(1, 0))
        for n in range(10):                                  # 1-9 and 0 open the first ten cells
            self.bind(digit_key((n + 1) % 10), lambda i=n: self.pick(i))
        self.bind(K.Key_Enter, self.enter_action)            # ahead of BaseGame's "play again"
        self.bind(K.Key_Return, self.enter_action)
        self.bind(K.Key_Space, self.space_action)

        self.set_risk('medium')

    # ---- controls
    def set_risk(self, risk):
        if self.picks or self.done:
            return
        self.risk = risk
        self.mines = rules.mines_layout(rules.MINES_RISK[risk], self.rng)
        self.reset()

    def reset(self):
        self.picks, self.mult, self.cursor = 0, 1.0, 0
        self.tiles = ['hidden'] * (SIDE * SIDE)
        for i, b in enumerate(self.cells):
            b.setEnabled(True)
            b.setStyleSheet(tile_style('hidden', cursor=(i == 0)))
        self.cash_btn.setEnabled(False)
        for b in self.risk_btns.values():
            b.setEnabled(True)
        self.auto_chk.setEnabled(True)
        self.auto_spin.setEnabled(True)
        self.refresh()

    def move(self, dx, dy):
        if self.done:
            return
        r, c = divmod(self.cursor, SIDE)
        r = max(0, min(SIDE - 1, r + dy))
        c = max(0, min(SIDE - 1, c + dx))
        self.set_cursor(r * SIDE + c)

    def set_cursor(self, i):
        if i == self.cursor:
            return
        old, self.cursor = self.cursor, i
        self.paint(old)
        self.paint(i)

    def paint(self, i):
        self.cells[i].setStyleSheet(tile_style(self.tiles[i], cursor=(i == self.cursor)))

    def enter_action(self):
        if self.done:                                        # BaseGame's bindings sit behind ours
            if self.again_btn.isVisible():
                self.again_btn.click()
        else:
            self.pick(self.cursor)

    def space_action(self):
        if self.done:
            if self.again_btn.isVisible():
                self.again_btn.click()
        elif self.picks:
            self.cash_out()
        else:
            self.pick(self.cursor)

    # ---- the round
    def pick(self, i):
        if self.done or self.tiles[i] != 'hidden':
            return
        if not self.in_progress:
            self.lock(True)                                  # once you have touched the board you stay
            for b in self.risk_btns.values():
                b.setEnabled(False)
            self.auto_chk.setEnabled(False)                  # the auto target is locked in with your first pick
            self.auto_spin.setEnabled(False)
        self.cells[i].setEnabled(False)
        self.tiles[i] = 'mine' if i in self.mines else 'safe'
        self.paint(i)
        if self.tiles[i] == 'mine':
            self.explode(i)
            self.stop(rules.settle_mines(self.mult, self.bet, boom=True))
            return
        self.picks += 1
        self.mult = rules.mines_multiplier(self.picks, rules.MINES_RISK[self.risk], edge=self.edge)
        self.cash_btn.setEnabled(True)
        self.uncover_anim(i)
        if self.picks == SIDE * SIDE - rules.MINES_RISK[self.risk]:
            self.stop(rules.settle_mines(self.mult, self.bet, cleared=True))
            return
        self.refresh()
        if self.auto_chk.isChecked() and self.mult >= self.auto_spin.value():
            self.cash_out()                                  # the target you set before the round

    # ---- animations (purely visual)
    def uncover_anim(self, i):
        """A green sparkle over a safe cell, and the multiplier ticking up."""
        self.burst_on(self.cells[i], 0.5, 0.5, n=8, colors=['#5ad39b', '#a7f3cf'],
                      speed=(0.8, 2.4), gravity=0.2, size=(2, 5), life=(20, 34))
        self.pulse(self.mult_lbl, 'color:#ffe9a3; font-size:34px;', 260)

    def explode(self, i):
        """Boom: a red flash, a shockwave and a cloud of sparks over the mine."""
        self.fx_flash('#ff5a5a', 70, 360)
        self.fx_flash('#ffffff', 90, 140)
        self.ring_on(self.cells[i], 0.5, 0.5, color='#ff8a8a', r1=140, width=5, ms=420)
        self.burst_on(self.cells[i], 0.5, 0.5, n=30, colors=['#ff6b6b', '#ffb35c', '#ffe9a3', '#e8eaf0'],
                      speed=(2.0, 8.0), gravity=0.25, size=(3, 8), life=(34, 66))

    def cash_out(self):
        if self.done or self.picks == 0:
            return
        self.stop(rules.settle_mines(self.mult, self.bet))

    def stop(self, outcome):
        self.done = True
        rest = [i for i in self.mines if self.tiles[i] == 'hidden']
        for i in rest:                                       # show what you were walking through
            self.tiles[i] = 'mine'
            self.cells[i].setEnabled(False)
        self.cash_btn.setEnabled(False)
        for b in self.risk_btns.values():
            b.setEnabled(False)
        self.mult_lbl.setText(f'{self.mult:g}×')
        # the hidden mines light up one by one, each with a red pulse
        if self.app.settings.effects and self.app.anim_factor() > 0 and rest:
            for n, i in enumerate(rest):
                self.after(90 * n, lambda i=i: (self.paint(i), self.pulse(self.cells[i], self._mine_css(), 200)))
            self.after(90 * len(rest), lambda: self.finish_with(outcome))
        else:
            for i in rest:
                self.paint(i)
            self.finish_with(outcome)

    @staticmethod
    def _mine_css():
        return ('QPushButton, QPushButton:disabled {background:qlineargradient(x1:0,y1:0,x2:0,y2:1,'
                'stop:0 #ff8a8a,stop:1 #b3261e);color:#2a0000;border:3px solid #ffd0d0;border-radius:9px;'
                'font-size:26px;font-weight:700;}')

    def refresh(self):
        self.mult_lbl.setText(f'{self.mult:g}×')
        if self.done:
            return
        cells = SIDE * SIDE
        mines = rules.MINES_RISK[self.risk]
        if not self.picks:
            self.info.setText(f'{mines} mines hide in {cells} cells. Arrows move, Enter opens a cell, '
                              'Space picks your first one.')
            return
        win = int(self.bet * self.mult) - self.bet
        nxt = rules.mines_multiplier(self.picks + 1, mines, edge=self.edge)
        self.info.setText(f'{self.picks} safe  •  cash out {"+" if win > 0 else ""}{win:,} TL'
                          f'  •  one more cell {nxt:g}×  •  Enter for another'
                          + (f'  •  auto at {self.auto_spin.value():g}×'
                             if self.auto_chk.isChecked() else ''))
