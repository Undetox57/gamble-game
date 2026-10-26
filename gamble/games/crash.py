"""Crash: a multiplier climbs until it crashes. Cash out before that to win bet x multiplier."""
import math

from PyQt6.QtCore import QPointF, QPoint, QRectF, Qt, QTimer
from PyQt6.QtGui import QColor, QFont, QLinearGradient, QPainter, QPen, QPolygonF
from PyQt6.QtWidgets import (QCheckBox, QDoubleSpinBox, QGraphicsDropShadowEffect, QHBoxLayout, QLabel,
                             QWidget)

from .. import rules
from ..fx import VRNG
from ..widgets import AC, Button, centered
from .base import BaseGame, K

GROWTH = 0.14          # the multiplier is exp(GROWTH * seconds): 2x after ~5 s, 10x after ~16 s


class CrashGraph(QWidget):
    def __init__(self):
        super().__init__()
        self.setMinimumHeight(190)
        self.pts = [(0.0, 1.0)]
        self.crashed = False
        self.cash_mark = None          # (t, multiplier) where you cashed out
        self.shake = 0.0               # horizontal jitter while the round is crashing

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        if self.shake:                                    # the graph rattles when it blows up
            p.translate(VRNG.uniform(-1, 1) * self.shake, VRNG.uniform(-1, 1) * self.shake * 0.5)
        ml, mr, mt, mb = 50, 14, 10, 22
        tmax = max(6.0, self.pts[-1][0])
        mmax = max(2.0, max(m for _, m in self.pts) * 1.15)
        font = QFont(p.font())
        font.setPointSize(9)
        p.setFont(font)

        def X(t):
            return ml + t / tmax * (w - ml - mr)

        def Y(m):
            return h - mb - (m - 1) / (mmax - 1) * (h - mb - mt)

        for i in range(4):
            m = 1 + (mmax - 1) * i / 3
            p.setPen(QPen(QColor(255, 255, 255, 30), 1))
            p.drawLine(QPointF(ml, Y(m)), QPointF(w - mr, Y(m)))
            p.setPen(QColor('#9fb8ac'))
            p.drawText(QRectF(0, Y(m) - 9, ml - 6, 18), Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                       f'{m:.1f}×')
        pts = [QPointF(X(t), Y(m)) for t, m in self.pts]
        color = QColor('#ff6b6b' if self.crashed else '#4cc38a')
        if len(pts) > 1:                                     # soft glow + gradient fill under the curve
            base = Y(1.0)
            area = QPolygonF(pts + [QPointF(pts[-1].x(), base), QPointF(pts[0].x(), base)])
            grad = QLinearGradient(QPointF(0, mt), QPointF(0, base))
            fill = QColor(color)
            fill.setAlpha(70)
            grad.setColorAt(0.0, fill)
            clear = QColor(color)
            clear.setAlpha(0)
            grad.setColorAt(1.0, clear)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(grad)
            p.drawPolygon(area)
            p.setPen(QPen(color, 3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
            p.drawPolyline(QPolygonF(pts))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(color)
        p.drawEllipse(pts[-1], 5, 5)
        if self.cash_mark:
            p.setBrush(QColor('#f4c542'))
            p.drawEllipse(QPointF(X(self.cash_mark[0]), Y(self.cash_mark[1])), 6, 6)


class CrashGame(BaseGame):
    key, title = 'crash', 'Crash'

    def build(self):
        self.crash_at = rules.crash_point(self.rng, self.edge)
        self.t, self.mult = 0.0, 1.0
        self.running, self.cashed = False, None
        self.part = None                    # (multiplier, stake) already banked by a half cash-out
        self.big = QLabel('1.00×')
        self.big.setAlignment(AC)
        self._glow, self._big_color = None, None        # the glow is built once and only recoloured
        self.set_big('#e8eaf0')
        self.body.addWidget(self.big)
        self.graph = CrashGraph()
        self.body.addWidget(self.graph, 1)
        self.note = centered(f'Press START, then CASH OUT before it crashes. {self.edge * 100:.0f}% of '
                             f'rounds crash instantly.', 'hint')
        self.body.addWidget(self.note)
        auto = QHBoxLayout()
        auto.addStretch()
        self.auto_chk = QCheckBox('Auto cash-out at')
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
        half = QHBoxLayout()
        half.addStretch()
        self.half_chk = QCheckBox('Cash out half at')
        self.half_spin = QDoubleSpinBox()
        self.half_spin.setRange(1.01, 1000.0)
        self.half_spin.setDecimals(2)
        self.half_spin.setSingleStep(0.25)
        self.half_spin.setValue(1.5)
        self.half_spin.setSuffix('×')
        half.addWidget(self.half_chk)
        half.addWidget(self.half_spin)
        half.addWidget(QLabel('— the rest keeps riding'))
        half.addStretch()
        self.body.addLayout(half)
        row = QHBoxLayout()
        self.go_btn = Button('START  [Space]')
        self.go_btn.setObjectName('primary')
        self.cash_btn = Button('CASH OUT  [Space]')
        self.cash_btn.setEnabled(False)
        for b in (self.go_btn, self.cash_btn):
            b.setMinimumHeight(52)
            row.addWidget(b)
        self.go_btn.clicked.connect(self.start)
        self.cash_btn.clicked.connect(self.cash_out)
        self.body.addLayout(row)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.shake_timer = None
        self.bind(K.Key_Space, self.go_btn)
        self.bind(K.Key_Space, self.cash_btn)

    def set_big(self, color):
        """Colour the big multiplier. The glow effect is created once and only recoloured after
        that: rebuilding the effect (and re-polishing the stylesheet) on every 40 ms frame made
        the number blink and sometimes vanish for good."""
        if color == self._big_color:
            return
        self._big_color = color
        self.big.setStyleSheet(f'color:{color};font-size:64px;font-weight:800;')
        if not (self.effects_on() and self.app.anim_factor() > 0):
            if self._glow is not None:
                self.big.setGraphicsEffect(None)        # effects were switched off mid-round
                self._glow = None
            return
        if self._glow is None:
            glow = QGraphicsDropShadowEffect(self.big)
            glow.setBlurRadius(34)
            glow.setOffset(0, 0)
            self.big.setGraphicsEffect(glow)
            self._glow = glow
        self._glow.setColor(QColor(color))

    def speed(self):
        f = self.app.anim_factor()           # animation setting: Normal / Fast / Instant
        return 1.0 if f >= 1 else 2.0 if f >= 0.5 else 4.0

    def start(self):
        self.go_btn.setEnabled(False)
        for w in (self.auto_chk, self.auto_spin, self.half_chk, self.half_spin):
            w.setEnabled(False)
        self.lock(True)
        self.running = True
        if self.crash_at <= 1.0:
            self.do_crash()
            return
        self.cash_btn.setEnabled(True)
        self.timer.start(40)

    def tick(self):
        dt = 0.04 * self.speed() * (4 if self.cashed is not None else 1)     # after cashing out: fast-forward
        self.t += dt
        self.mult = math.exp(GROWTH * self.t)
        m = math.floor(self.mult * 100) / 100
        if m >= self.crash_at:
            self.do_crash()
            return
        self.graph.pts.append((self.t, self.mult))
        self.graph.update()
        self.big.setText(f'{m:.2f}×')
        if self.cashed is None:
            self.set_big('#4cc38a' if m < 2 else '#f4c542')
            if self.part is None and self.half_chk.isChecked() and m >= self.half_spin.value():
                self.half_out(m)                       # bank half, let the rest keep riding
            if self.auto_chk.isChecked() and m >= self.auto_spin.value():
                self.cash_out()

    def half_out(self, m):
        """Bake half the stake at the current multiplier; the remainder keeps playing."""
        stake = self.bet // 2
        if self.part is not None or not self.running or stake < 1:
            return
        self.part = (m, stake)
        self.half_chk.setChecked(False)
        self.note.setText(f'Half banked at {m:.2f}× ({stake:,} TL). The rest is still riding...')
        if self.effects_on():
            gx = 50 + (self.t / max(6.0, self.t)) * (self.graph.width() - 64)
            base = self.graph.height() - 22
            gy = base - (m - 1) / max(1.0, max(2.0, m * 1.15) - 1) * (base - 10)
            pt = self.graph.mapTo(self.felt, QPoint(round(gx), round(gy)))
            self.fx.ring(pt.x(), pt.y(), r0=6, r1=70, color='#ffe9a3', ms=380, width=3)
        self.pulse(self.big, 'color:#ffe9a3; font-size:64px;', 240)

    def settle_round(self, cashed):
        """(delta, win, text, tags) for the whole round, half cash-out or not.

        Each part goes through the very same rules.settle_crash, so splitting the stake cannot
        change what the game pays - it only lets you bank part of the win early."""
        if self.part is None:
            return rules.settle_crash(cashed, self.crash_at, self.bet)
        p_mult, p_stake = self.part
        part = rules.settle_crash(p_mult, self.crash_at, p_stake)
        tail = rules.settle_crash(cashed, self.crash_at, self.bet - p_stake)
        delta = part[0] + tail[0]
        win = True if delta > 0 else False if delta < 0 else None
        tags = tuple(dict.fromkeys(part[3] + tail[3]))
        head = f'Half banked at {p_mult:.2f}×, '
        if cashed is None:
            head += f'the rest crashed at {self.crash_at:.2f}×.'
        else:
            head += f'the rest cashed out at {cashed:.2f}×.'
        return delta, win, head, tags

    def cash_out(self):
        if not self.running or self.cashed is not None:
            return
        m = math.floor(self.mult * 100) / 100
        self.cashed = m
        self.cash_btn.setEnabled(False)
        self.graph.cash_mark = (self.t, self.mult)
        self.set_big('#f4c542')
        if self.effects_on():                             # a gold ring blooms where you got out
            gx = 50 + (self.t / max(6.0, self.t)) * (self.graph.width() - 64)
            base = self.graph.height() - 22
            gy = base - (m - 1) / max(1.0, max(2.0, m * 1.15) - 1) * (base - 10)
            pt = self.graph.mapTo(self.felt, QPoint(round(gx), round(gy)))
            self.fx.ring(pt.x(), pt.y(), r0=6, r1=90, color='#f4c542', ms=420, width=4)
            self.fx.burst(pt.x(), pt.y(), n=18, colors=['#f4c542', '#ffe9a3'], speed=(1.4, 4.5),
                          gravity=0.12, size=(3, 6))
        self.finish_with(self.settle_round(m))
        if self.part is None:
            self.note.setText('Cashed out! Watching where the round would have crashed...')
        else:
            self.note.setText('The rest is banked too - watching where it would have crashed...')

    def do_crash(self):
        self.timer.stop()
        self.running = False
        self.cash_btn.setEnabled(False)
        self.graph.crashed = True
        self.graph.pts.append((max(self.t, 0.01), self.crash_at))
        self.graph.update()
        self.big.setText(f'{self.crash_at:.2f}×')
        self.start_shake()
        self.fx_flash('#ff6b6b', 55, 360)
        self.fx_flash('#ffffff', 80, 130)
        if self.cashed is None:
            self.set_big('#ff6b6b')
            self.finish_with(self.settle_round(None))
            self.note.setText('CRASHED!')
        else:
            self.note.setText(f'The round crashed at {self.crash_at:.2f}×.')

    def start_shake(self):
        """Rattle the graph for a few tenths of a second."""
        if not (self.effects_on() and self.app.anim_factor() > 0):
            return
        state = {'amp': 9.0}

        def tick():
            state['amp'] *= 0.72
            self.graph.shake = state['amp']
            self.graph.update()
            if state['amp'] < 0.5:
                self.shake_timer.stop()
                self.graph.shake = 0.0
                self.graph.update()
        self.shake_timer = QTimer(self)
        self.shake_timer.timeout.connect(tick)
        self.shake_timer.start(40)
