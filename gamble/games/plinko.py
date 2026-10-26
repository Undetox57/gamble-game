"""Plinko: drop a ball through the pegs. Three risk levels with different slot multipliers."""
import math

from PyQt6.QtCore import QPointF, QRectF, Qt, QTimer
from PyQt6.QtGui import QColor, QFont, QLinearGradient, QPainter, QPen
from PyQt6.QtWidgets import QButtonGroup, QHBoxLayout, QWidget

from .. import rules
from ..fx import VRNG
from ..widgets import AC, Button, centered
from .base import BaseGame, K

CX, DX, DY, TOP = 240, 46, 31, 26        # board geometry (pixels)
SLOT_Y = TOP + 22 + rules.PLINKO_ROWS * DY + 8


def slot_color(m):
    return '#7b4fb8' if m >= 5 else '#c9a227' if m >= 2 else '#2e8b57' if m >= 1 else '#6b2330'


class PlinkoBoard(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedSize(480, SLOT_Y + 44)
        self.risk = 'medium'
        self.ball = None             # (x, y) while falling
        self.trail = []              # recent ball positions, for the falling glow
        self.hit_slot = None
        self.flashes = {}            # (row, index) -> remaining glow of a struck peg
        self.pop = 0.0               # how much the winning slot is bouncing (0 = flat)

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)
        for r in range(rules.PLINKO_ROWS):
            for j in range(r + 1):
                hot = self.flashes.get((r, j), 0)
                if hot:                                   # a peg the ball just bounced off lights up
                    p.setBrush(QColor(244, 197, 66, min(255, 60 + hot * 40)))
                    p.drawEllipse(QPointF(CX + (j - r / 2) * DX, TOP + 22 + r * DY), 6, 6)
                else:
                    p.setBrush(QColor(255, 255, 255, 170))
                    p.drawEllipse(QPointF(CX + (j - r / 2) * DX, TOP + 22 + r * DY), 4, 4)
        font = QFont(p.font())
        font.setBold(True)
        font.setPointSize(10)
        p.setFont(font)
        for k, m in enumerate(rules.PLINKO_TABLES[self.risk]):
            grow = self.pop * 9 if k == self.hit_slot else 0     # the winning slot bounces up
            rect = QRectF(CX + (k - 4) * DX - DX / 2 + 2, SLOT_Y - grow, DX - 4, 34 + grow * 2)
            grad = QLinearGradient(rect.topLeft(), rect.bottomLeft())
            base = QColor(slot_color(m))
            light = base.lighter(145)
            grad.setColorAt(0.0, light)
            grad.setColorAt(1.0, base)
            p.setBrush(grad)
            p.setPen(QPen(QColor('#ffe9a3'), 3) if k == self.hit_slot else QPen(QColor('#1a1a1a'), 1))
            p.drawRoundedRect(rect, 6, 6)
            p.setPen(QColor('white'))
            p.drawText(rect, AC, f'{m:g}×')
        if self.trail:                                     # fading glow behind the ball
            for i, (tx, ty) in enumerate(self.trail):
                a = int(60 * (i + 1) / len(self.trail))
                p.setBrush(QColor(244, 197, 66, a))
                p.drawEllipse(QPointF(tx, ty), 6, 6)
        if self.ball:
            p.setPen(QPen(QColor('#7a5c00'), 2))
            p.setBrush(QColor('#f4c542'))
            p.drawEllipse(QPointF(*self.ball), 8, 8)


class PlinkoGame(BaseGame):
    key, title = 'plinko', 'Plinko'

    def build(self):
        self.risk = 'medium'
        self.board = PlinkoBoard()
        self.body.addWidget(self.board, 0, AC)
        self.body.addWidget(centered('Pick a risk level, then drop the ball. Higher risk = bigger corners.', 'prompt'))
        row = QHBoxLayout()
        self.group = QButtonGroup(self)
        self.risk_btns = {}
        for r, label, key in (('low', 'Low  [L]', K.Key_L), ('medium', 'Medium  [M]', K.Key_M),
                              ('high', 'High  [H]', K.Key_H)):
            b = Button(label)
            b.setCheckable(True)
            b.setMinimumHeight(40)
            b.setChecked(r == 'medium')
            b.clicked.connect(lambda _=False, r=r: self.set_risk(r))
            self.group.addButton(b)
            row.addWidget(b)
            self.risk_btns[r] = b
            self.bind(key, b)
        self.body.addLayout(row)
        self.drop_btn = Button('DROP BALL  [Space]')
        self.drop_btn.setObjectName('primary')
        self.drop_btn.setMinimumHeight(50)
        self.drop_btn.clicked.connect(self.drop)
        self.body.addWidget(self.drop_btn)
        self.bind(K.Key_Space, self.drop_btn)

    def set_risk(self, risk):
        self.risk = risk
        self.board.risk = risk
        self.board.update()

    def drop(self):
        self.drop_btn.setEnabled(False)
        for b in self.risk_btns.values():
            b.setEnabled(False)
        self.lock(True)
        self.pop_timer = None
        path = rules.plinko_path(self.rng)
        pts, off = [(CX, TOP)], 0.0
        for r, right in enumerate(path):
            off += 0.5 if right else -0.5
            y = TOP + 22 + (r + 1) * DY if r < rules.PLINKO_ROWS - 1 else SLOT_Y + 17
            pts.append((CX + off * DX, y))
        frames = 7

        def tick(n):
            seg, s = divmod(n - 1, frames)
            s = (s + 1) / frames
            (x0, y0), (x1, y1) = pts[seg], pts[seg + 1]
            pos = (x0 + (x1 - x0) * s, y0 + (y1 - y0) * s - 9 * math.sin(math.pi * s))
            self.board.ball = pos
            self.board.trail.append(pos)
            self.board.trail = self.board.trail[-9:]
            if s < 0.5 and self.app.settings.effects:        # the peg it just left glows
                r = min(seg, rules.PLINKO_ROWS - 1)
                j = round((x0 - CX) / DX + r / 2)
                self.board.flashes[(r, max(0, min(r, j)))] = 6
            for key in list(self.board.flashes):             # ...and fades away
                self.board.flashes[key] -= 1
                if self.board.flashes[key] <= 0:
                    del self.board.flashes[key]
            self.board.update()

        def done():
            self.board.ball = pts[-1]
            self.board.trail = []
            self.board.hit_slot = sum(path)
            self.board.update()
            self.burst_on(self.board, (CX + (self.board.hit_slot - 4) * DX) / self.board.width(),
                          SLOT_Y / self.board.height(), n=16,
                          colors=['#f4c542', '#ffe9a3', '#4cc38a'], speed=(1.0, 3.2), gravity=0.3,
                          size=(3, 6))
            self.pop_slot()
            self.finish_with(rules.settle_plinko(path, self.risk, self.bet))
        self.animate(rules.PLINKO_ROWS * frames + 1, 24, tick, done)

    def pop_slot(self):
        """The winning slot bounces up and settles back."""
        if not (self.effects_on() and self.app.anim_factor() > 0):
            return
        state = {'a': 1.0}

        def tick():
            state['a'] *= 0.7
            self.board.pop = state['a']
            self.board.update()
            if state['a'] < 0.05:
                self.pop_timer.stop()
                self.board.pop = 0.0
                self.board.update()
        self.pop_timer = QTimer(self)
        self.pop_timer.timeout.connect(tick)
        self.pop_timer.start(40)
