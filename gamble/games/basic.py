"""The simple one-click games: coin flip, dice, slot machine, wheel of fortune, scratch card."""
import math

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QLinearGradient, QPainter, QPen, QPolygonF
from PyQt6.QtWidgets import QGridLayout, QHBoxLayout, QLabel, QWidget

from .. import rules
from ..fx import VRNG
from ..widgets import AC, Button, centered
from .base import BaseGame, K, digit_key


class CoinGame(BaseGame):
    key, title = 'coin', 'Coin Flip'

    def build(self):
        self.body.addStretch()
        self.coin = QLabel('?')
        self.coin.setFixedSize(130, 130)
        self.coin.setAlignment(AC)
        self.set_face(None)
        self.body.addWidget(self.coin, 0, AC)
        self.body.addWidget(centered('Heads or Tails?  [H / T]', 'prompt'))
        row = QHBoxLayout()
        self.btns = []
        for label, g in (('Heads', 'h'), ('Tails', 't')):
            b = Button(label)
            b.setObjectName('primary')
            b.setMinimumHeight(48)
            b.clicked.connect(lambda _=False, g=g: self.pick(g))
            row.addWidget(b)
            self.btns.append(b)
        self.body.addLayout(row)
        self.body.addStretch()
        self.bind(K.Key_H, self.btns[0])
        self.bind(K.Key_1, self.btns[0])
        self.bind(K.Key_T, self.btns[1])
        self.bind(K.Key_2, self.btns[1])

    def set_face(self, f):
        self.coin.setText({'h': 'H', 't': 'T'}.get(f, '?'))
        self.coin.setStyleSheet(
            'background:qradialgradient(cx:0.35, cy:0.3, radius:0.9, stop:0 #ffe9a3, stop:0.55 #f4c542,'
            ' stop:1 #a8790a);color:#3a2a00;border:6px solid #f4c542;border-radius:65px;'
            'font-size:58px;font-weight:800;')

    def pick(self, guess):
        for b in self.btns:
            b.setEnabled(False)
        self.lock(True)
        result = rules.coin_flip(self.rng)

        def tick(n):
            # the coin turns edge-on and back: the label squashes horizontally while it flips
            self.set_face('h' if n % 2 else 't')
            if self.app.settings.effects and self.app.anim_factor() > 0:
                w = max(8, round(130 * abs(math.cos(n * 0.55))))
                self.coin.setFixedWidth(w)

        def done():
            self.coin.setFixedWidth(130)
            self.set_face(result)
            self.burst_on(self.coin, 0.5, 0.9, n=10, colors=['#f4c542', '#ffe9a3'],
                          speed=(0.8, 2.6), gravity=0.35, size=(2, 5))
            self.finish_with(rules.settle_coin(guess, result, self.bet))
        self.animate(12, 90, tick, done)


class DiceGame(BaseGame):
    key, title = 'dice', 'Dice Roll'

    def build(self):
        self.body.addStretch()
        self.face = QLabel('?')
        self.face.setFixedSize(120, 120)
        self.face.setAlignment(AC)
        self.face.setStyleSheet(
            'background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #ffffff,stop:1 #dfe4ec);'
            'color:#111;border:2px solid #cfd6e2;border-radius:18px;font-size:68px;font-weight:800;')
        self.body.addWidget(self.face, 0, AC)
        self.body.addWidget(centered('Guess a number between 1 and 6  [1-6]', 'prompt'))
        row = QHBoxLayout()
        self.btns = []
        for n in range(1, 7):
            b = Button(str(n))
            b.setMinimumHeight(50)
            b.clicked.connect(lambda _=False, n=n: self.pick(n))
            row.addWidget(b)
            self.btns.append(b)
            self.bind(digit_key(n), b)
        self.body.addLayout(row)
        self.body.addStretch()

    def pick(self, guess):
        for b in self.btns:
            b.setEnabled(False)
        self.lock(True)
        roll = self.rng.randint(1, 6)
        origin = None                                    # where the dice flies from and back to

        def tick(n):
            nonlocal origin
            self.face.setText(str(VRNG.randint(1, 6)))
            if not (self.app.settings.effects and self.app.anim_factor() > 0):
                return
            if origin is None:
                origin = self.face.pos()
            x, y = origin
            t = n / 14
            self.face.move(round(x + 150 * math.sin(t * math.pi)),      # a parabola over the table
                           round(y - 90 * math.sin(t * math.pi)))

        def done():
            if origin is not None:
                self.face.move(origin)
            self.face.setText(str(roll))
            self.fx_flash('#ffffff', 40, 160)            # a little puff as it lands
            self.burst_on(self.face, 0.5, 0.95, n=8, colors=['#dfe4ec', '#cfd6e2'],
                          speed=(0.6, 2.2), gravity=0.4, size=(2, 4), life=(18, 30))
            self.finish_with(rules.settle_dice(guess, roll, self.bet))
        self.animate(14, 80, tick, done)


SLOT_SYMBOLS = {'A': '🍒', 'B': '🍋', 'C': '🔔', 'D': '⭐', 'E': '🍇'}


class SlotGame(BaseGame):
    key, title = 'slot', 'Slot Machine'

    def build(self):
        self.body.addStretch()
        row = QHBoxLayout()
        row.setAlignment(AC)
        self.reels = []
        for _ in range(3):
            r = QLabel('❔')
            r.setFixedSize(120, 140)
            r.setAlignment(AC)
            r.setStyleSheet(
                'background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #ffffff,stop:1 #e3e7ee);'
                'color:#111;border:4px solid #d4a017;border-radius:14px;font-size:62px;')
            row.addWidget(r)
            self.reels.append(r)
        self.body.addLayout(row)
        self.body.addWidget(centered('Match 3 → 5×   •   Match 2 → 1.5×', 'prompt'))
        self.spin_btn = Button('SPIN  [Space]')
        self.spin_btn.setObjectName('primary')
        self.spin_btn.setMinimumHeight(52)
        self.spin_btn.clicked.connect(self.spin)
        self.body.addWidget(self.spin_btn)
        self.body.addStretch()
        self.bind(K.Key_Space, self.spin_btn)

    def spin(self):
        self.spin_btn.setEnabled(False)
        self.lock(True)
        final = rules.slot_spin(self.rng)
        stop_at = [12, 20, 28]
        origin = None

        def tick(n):
            nonlocal origin
            for i in range(3):
                sym = final[i] if n >= stop_at[i] else VRNG.choice(rules.SLOT_KEYS)
                self.reels[i].setText(SLOT_SYMBOLS[sym])
            if not (self.app.settings.effects and self.app.anim_factor() > 0):
                return
            if origin is None:
                origin = [r.pos().y() for r in self.reels]
            for i in range(3):                            # each reel gets a small bounce as it lands
                over = n - stop_at[i]
                dy = 0 if over < 0 else max(0, 10 - over * 3)
                self.reels[i].move(self.reels[i].pos().x(), origin[i] + dy)

        def done():
            if origin is not None:
                for i in range(3):
                    self.reels[i].move(self.reels[i].pos().x(), origin[i])
            for i in range(3):
                self.reels[i].setText(SLOT_SYMBOLS[final[i]])
            wins = [i for i in range(3) if final.count(final[i]) >= 2]
            for i in wins:                                    # light up the paying reels
                self.reels[i].setStyleSheet(
                    'background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #fff6d0,stop:1 #ffe9a3);'
                    'color:#111;border:4px solid #f4c542;border-radius:14px;font-size:62px;')
            if len(set(final)) == 1:                          # jackpot: coins rain over the machine
                self.fx_flash('#f4c542', 45, 380)
                for r in self.reels:
                    self.burst_on(r, 0.5, 0.2, n=14, colors=['#f4c542', '#ffe9a3', '#d4a017'],
                                  speed=(1.2, 3.4), gravity=0.45, size=(3, 6), life=(34, 60))
            self.finish_with(rules.settle_slot(final, self.bet))
        self.animate(28, 70, tick, done)


WHEEL_COLORS = {0: '#6b2330', 0.5: '#a8612a', 1: '#3d5a80', 2: '#2e8b57', 3: '#c9a227', 4: '#7b4fb8'}


class WheelWidget(QWidget):
    R = 150

    def __init__(self):
        super().__init__()
        self.setFixedSize(330, 340)
        self.angle = 0.0
        self.highlight = None          # index of the winning slice, once the round is over
        self.wobble = 0.0              # pointer twitch while the wheel is turning
        self.top_idx = None            # slice currently under the pointer

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        cx, cy, r = 165, 24 + self.R, self.R
        p.translate(cx, cy)
        font = p.font()
        font.setBold(True)
        font.setPointSize(13)
        p.setFont(font)
        for i, m in enumerate(rules.WHEEL_SEGMENTS):
            p.save()
            p.rotate(self.angle + i * 30)
            p.setBrush(QColor(WHEEL_COLORS[m]))
            p.setPen(QPen(QColor('#1a1a1a'), 2))
            p.drawPie(QRectF(-r, -r, 2 * r, 2 * r), 90 * 16, -30 * 16)
            if self.top_idx == i and self.highlight is None:   # slice passing under the pointer
                p.setBrush(QColor(255, 255, 255, 40))
                p.setPen(Qt.PenStyle.NoPen)
                p.drawPie(QRectF(-r, -r, 2 * r, 2 * r), 90 * 16, -30 * 16)
            p.restore()
            p.save()
            p.rotate(self.angle + i * 30 + 15)
            p.setPen(QColor('white'))
            p.drawText(QRectF(-30, -r + 12, 60, 30), AC, rules.WHEEL_LABELS[m])
            p.restore()
            if self.highlight == i:                       # gold ring around the winning slice
                p.save()
                p.rotate(self.angle + i * 30)
                p.setBrush(Qt.BrushStyle.NoBrush)
                p.setPen(QPen(QColor('#ffe9a3'), 5))
                p.drawArc(QRectF(-r + 3, -r + 3, 2 * r - 6, 2 * r - 6), 90 * 16, -30 * 16)
                p.restore()
        hub = QLinearGradient(QPointF(-18, -18), QPointF(18, 18))
        hub.setColorAt(0, QColor('#4a5570'))
        hub.setColorAt(1, QColor('#1a1a1a'))
        p.setBrush(hub)
        p.setPen(QPen(QColor('#f4c542'), 3))
        p.drawEllipse(QPointF(0, 0), 18, 18)
        p.resetTransform()
        p.translate(cx, 6)                                # the pointer, twitching as slices go by
        p.rotate(self.wobble)
        p.setBrush(QColor('#f4c542'))
        p.setPen(QPen(QColor('#1a1a1a'), 2))
        p.drawPolygon(QPolygonF([QPointF(-15, 0), QPointF(15, 0), QPointF(0, 28)]))


class WheelGame(BaseGame):
    key, title = 'wheel', 'Wheel of Fortune'

    def build(self):
        self.wheel = WheelWidget()
        self.body.addWidget(self.wheel, 0, AC)
        self.body.addWidget(centered('Spin the wheel! Slices pay between 0× and 4× your bet.', 'prompt'))
        self.spin_btn = Button('SPIN  [Space]')
        self.spin_btn.setObjectName('primary')
        self.spin_btn.setMinimumHeight(48)
        self.spin_btn.clicked.connect(self.spin)
        self.body.addWidget(self.spin_btn)
        self.bind(K.Key_Space, self.spin_btn)

    def spin(self):
        self.spin_btn.setEnabled(False)
        self.lock(True)
        seg = self.rng.randrange(len(rules.WHEEL_SEGMENTS))
        target = 360 * 6 - (seg * 30 + 15) + VRNG.uniform(-9, 9)
        steps = 90

        def tick(n):
            t = n / steps
            self.wheel.angle = target * (1 - (1 - t) ** 3)
            self.wheel.top_idx = next((i for i in range(len(rules.WHEEL_SEGMENTS))
                                       if (self.wheel.angle + i * 30) % 360 < 30), None)
            self.wheel.wobble = VRNG.uniform(-5, 5) * (1 - t)   # the pointer twitches while it spins
            self.wheel.update()

        def done():
            self.wheel.angle = target
            self.wheel.highlight = seg
            self.wheel.top_idx = None
            self.wheel.wobble = 0.0
            self.wheel.update()
            self.ring_on(self.wheel, 0.5, 0.45, color='#ffe9a3', r1=120, width=4, ms=380)
            self.finish_with(rules.settle_wheel(seg, self.bet))
        self.animate(steps, 40, tick, done)


class ScratchGame(BaseGame):
    key, title = 'scratch', 'Scratch Card'

    def build(self):
        self.mult = rules.scratch_roll(self.rng)
        self.win_sym, self.cells = rules.scratch_grid(self.mult, self.rng)
        self.revealed = [False] * 9
        self.pending = 0                       # cells still being scratched open
        self.body.addWidget(centered('Scratch the cells [1-9] or scratch all [A]. Find 3 matching symbols!', 'prompt'))
        prizes = '   '.join(f'{s} {m}×' for s, m in rules.SCRATCH_SYMBOLS.items())
        self.body.addWidget(centered(prizes, 'hint'))
        grid = QGridLayout()
        grid.setSpacing(8)
        self.btns = []
        for i in range(9):
            b = Button('?')
            b.setFixedSize(92, 92)
            b.setStyleSheet(
                'QPushButton{background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #b9c1cf,stop:1 #8d97a8);'
                'color:#4a5262;border:3px solid #cdd4e0;border-radius:12px;font-size:36px;font-weight:800;}'
                'QPushButton:hover{background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #c8cfdb,stop:1 #9aa4b5);}'
                'QPushButton:pressed{background:#7d8798;}')
            b.clicked.connect(lambda _=False, i=i: self.reveal(i))
            grid.addWidget(b, i // 3, i % 3)
            self.btns.append(b)
            self.bind(digit_key(i + 1), b)
        gw = QWidget()
        gw.setLayout(grid)
        self.body.addWidget(gw, 0, AC)
        self.all_btn = Button('Scratch all  [A]')
        self.all_btn.setMinimumHeight(44)
        self.all_btn.clicked.connect(self.reveal_all)
        self.body.addWidget(self.all_btn)
        self.bind(K.Key_A, self.all_btn)
        self.bind(K.Key_Space, self.all_btn)

    def reveal(self, i):
        if self.revealed[i]:
            return
        self.lock(True)
        self.revealed[i] = True
        b = self.btns[i]
        b.setEnabled(False)
        if not (self.app.settings.effects and self.app.anim_factor() > 0):
            b.setText(self.cells[i])
            self.paint_cell(b, False)
            if all(self.revealed):
                self.all_btn.setEnabled(False)
                self.resolve()
            return
        # scratch it open: the cell shows a dust smear for a moment, then the symbol
        self.pending += 1
        b.setText('▒')
        self.paint_cell(b, False)
        self.burst_on(b, VRNG.uniform(0.2, 0.8), 0.5, n=5, colors=['#c8cfdb', '#8d97a8'],
                      speed=(0.5, 1.8), gravity=0.3, size=(2, 4), life=(12, 22))
        self.after(110, lambda i=i: self.uncover(i))
        if all(self.revealed):
            self.all_btn.setEnabled(False)

    def uncover(self, i):
        self.btns[i].setText(self.cells[i])
        self.paint_cell(self.btns[i], False)
        self.pending -= 1
        if all(self.revealed) and self.pending <= 0:
            self.resolve()

    @staticmethod
    def paint_cell(b, win):
        if win:
            b.setStyleSheet(
                'QPushButton, QPushButton:disabled {background:qlineargradient(x1:0,y1:0,x2:0,y2:1,'
                'stop:0 #fff6d0,stop:1 #ffe08a);color:#111;border:4px solid #f4c542;border-radius:12px;'
                'font-size:38px;}')
        else:
            b.setStyleSheet(
                'QPushButton, QPushButton:disabled {background:qlineargradient(x1:0,y1:0,x2:0,y2:1,'
                'stop:0 #ffffff,stop:1 #e6eaf1);color:#111;border:4px solid #cfcfcf;border-radius:12px;'
                'font-size:38px;}')

    def reveal_all(self):
        self.all_btn.setEnabled(False)
        self.lock(True)
        for n, i in enumerate(i for i in range(9) if not self.revealed[i]):
            self.after(120 * (n + 1), lambda i=i: self.reveal(i))

    def resolve(self):
        if self.win_sym:
            for i, s in enumerate(self.cells):
                if s == self.win_sym:
                    self.paint_cell(self.btns[i], True)
            if self.app.settings.effects and self.app.anim_factor() > 0:
                for k, i in enumerate(i for i, s in enumerate(self.cells) if s == self.win_sym):
                    self.after(90 * k, lambda i=i: self.shine(self.btns[i]))
        self.finish_with(rules.settle_scratch(self.mult, self.win_sym, self.bet))

    def shine(self, b):
        """A quick gold flash travelling across a winning cell."""
        b.setStyleSheet(
            'QPushButton, QPushButton:disabled {background:qlineargradient(x1:0,y1:0,x2:1,y2:1,'
            'stop:0 #fffbe8,stop:1 #ffd75e);color:#111;border:4px solid #fff6d0;border-radius:12px;'
            'font-size:38px;}')
        self.burst_on(b, 0.5, 0.3, n=6, colors=['#ffe9a3', '#f4c542'], speed=(0.6, 2.0),
                      gravity=0.25, size=(2, 5), life=(18, 30))
        self.after(220, lambda: self.paint_cell(b, True))
