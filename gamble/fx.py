"""Reusable, purely-visual effects: particle bursts, shockwave rings, colour flashes,
floating numbers and cheap card flips.

Nothing in here touches the rules, the engine or the game state - it only draws.
Decoration gets its own RNG (VRNG) so animation frames can never shift a game's result.
"""
import math
import random

from PyQt6.QtCore import (QEasingCurve, QEvent, QParallelAnimationGroup, QPoint, QPropertyAnimation,
                          QSequentialAnimationGroup, QTimer, Qt)
from PyQt6.QtCore import QPointF, QRectF
from PyQt6.QtGui import QColor, QPainter, QPen
from PyQt6.QtWidgets import QGraphicsOpacityEffect, QLabel, QWidget

VRNG = random.Random()

PARTICLE_COLORS = ['#f4c542', '#4cc38a', '#ff6b6b', '#6c8cff', '#e8eaf0', '#b06ee0', '#3fc8e0']


class FxOverlay(QWidget):
    """Particles, expanding rings and full-cover colour flashes drawn over a host widget."""

    def __init__(self, host):
        super().__init__(host)
        self.host = host
        self.parts, self.rings, self.flashes = [], [], []
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.setGeometry(host.rect())
        host.installEventFilter(self)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.step)
        self.hide()

    def eventFilter(self, obj, event):
        if obj is self.host and event.type() == QEvent.Type.Resize:
            self.setGeometry(self.host.rect())
            self.raise_()
        return False

    # ---------------------------------------------------------------- API
    def burst(self, x, y, n=18, colors=None, speed=(2.0, 7.5), gravity=0.28, size=(3, 7), life=(28, 52)):
        colors = colors or PARTICLE_COLORS
        for _ in range(n):
            ang = VRNG.uniform(0, 2 * math.pi)
            sp = VRNG.uniform(*speed)
            self.parts.append({'x': float(x), 'y': float(y), 'vx': math.cos(ang) * sp,
                               'vy': math.sin(ang) * sp - 1.8, 'c': VRNG.choice(colors),
                               's': VRNG.uniform(*size), 'life': VRNG.randint(*life), 'max': life[1],
                               'g': gravity, 'a': VRNG.uniform(0, 360), 'spin': VRNG.uniform(-14, 14)})
        self._wake()

    def ring(self, x, y, r0=6.0, r1=70.0, color='#f4c542', ms=320, width=3):
        n = max(1, int(ms / 16))
        self.rings.append({'x': float(x), 'y': float(y), 'r0': r0, 'r1': r1, 'c': color,
                           'left': n, 'max': n, 'w': width})
        self._wake()

    def flash(self, color='#000000', alpha=70, ms=320):
        n = max(1, int(ms / 16))
        self.flashes.append({'c': QColor(color), 'a': alpha, 'left': n, 'max': n})
        self._wake()

    def clear(self):
        self.parts.clear()
        self.rings.clear()
        self.flashes.clear()
        self.timer.stop()
        self.hide()
        self.update()

    # ---------------------------------------------------------------- internals
    def _wake(self):
        self.raise_()
        self.show()
        if not self.timer.isActive():
            self.timer.start(16)

    def step(self):
        for p in self.parts:
            p['x'] += p['vx']
            p['y'] += p['vy']
            p['vy'] += p['g']
            p['vx'] *= 0.99
            p['a'] += p['spin']
            p['life'] -= 1
        self.parts = [p for p in self.parts if p['life'] > 0 and p['y'] < self.height() + 30]
        for r in self.rings:
            r['left'] -= 1
        self.rings = [r for r in self.rings if r['left'] > 0]
        for f in self.flashes:
            f['left'] -= 1
        self.flashes = [f for f in self.flashes if f['left'] > 0]
        self.update()
        if not (self.parts or self.rings or self.flashes):
            self.timer.stop()
            self.hide()

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        for r in self.rings:
            t = 1 - r['left'] / r['max']
            rad = r['r0'] + (r['r1'] - r['r0']) * (1 - (1 - t) ** 2)
            c = QColor(r['c'])
            c.setAlpha(int(210 * (1 - t)))
            p.setPen(QPen(c, r['w']))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawEllipse(QPointF(r['x'], r['y']), rad, rad)
        for pt in self.parts:
            t = pt['life'] / pt['max']
            c = QColor(pt['c'])
            c.setAlphaF(min(1.0, t * 1.6))
            p.save()
            p.translate(pt['x'], pt['y'])
            p.rotate(pt['a'])
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(c)
            p.drawRoundedRect(QRectF(-pt['s'] / 2, -pt['s'] * 0.35, pt['s'], pt['s'] * 0.7), 2, 2)
            p.restore()
        for f in self.flashes:
            c = QColor(f['c'])
            c.setAlpha(int(f['a'] * f['left'] / f['max']))
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(c)
            p.drawRect(self.rect())


def float_text(host, pos, text, color='#4cc38a', size=20, rise=36, ms=1200):
    """A small label that rises and fades away (deletes itself)."""
    lbl = QLabel(text, host)
    lbl.setStyleSheet(f'color:{color};font-size:{size}px;font-weight:800;background:transparent;')
    lbl.adjustSize()
    lbl.move(int(pos.x()) - lbl.width() // 2, int(pos.y()) - lbl.height() // 2)
    lbl.show()
    lbl.raise_()
    eff = QGraphicsOpacityEffect(lbl)
    lbl.setGraphicsEffect(eff)
    move = QPropertyAnimation(lbl, b'pos', lbl)
    move.setDuration(ms)
    start = lbl.pos()
    move.setStartValue(start)
    move.setEndValue(start + QPoint(0, -rise))
    move.setEasingCurve(QEasingCurve.Type.OutCubic)
    fade = QPropertyAnimation(eff, b'opacity', lbl)
    fade.setDuration(ms)
    fade.setStartValue(1.0)
    fade.setEndValue(0.0)
    fade.setEasingCurve(QEasingCurve.Type.InQuad)
    group = QParallelAnimationGroup(lbl)
    group.addAnimation(move)
    group.addAnimation(fade)
    group.finished.connect(lbl.deleteLater)
    group.start()
    return lbl


def alive(widget):
    """True while the widget's C++ object still exists.

    Pages are destroyed as soon as you leave them, so an animation that outlives its page must
    never touch a deleted widget again."""
    try:
        from PyQt6 import sip
    except Exception:                                   # cannot check - assume it is still there
        return True
    try:
        return not sip.isdeleted(widget)
    except Exception:                                   # the Python wrapper is already gone
        return False


def _detach(widget, eff):
    """Remove `eff` from `widget` - but only while it is still the widget's active effect,
    so a newer animation on the same widget is never killed by an older one finishing."""
    try:
        if widget.graphicsEffect() is eff:
            widget.setGraphicsEffect(None)
    except RuntimeError:                     # the widget is already gone
        pass


def _start(anim):
    try:
        anim.start()
    except RuntimeError:                     # the widget was deleted while we waited out the delay
        pass


def fade_in(widget, ms=220, delay=0):
    """Fade a freshly shown widget in (used when cards are dealt or revealed)."""
    eff = QGraphicsOpacityEffect(widget)
    eff.setOpacity(0.0)                      # invisible right away: no flash of the new face
    widget.setGraphicsEffect(eff)
    anim = QPropertyAnimation(eff, b'opacity', widget)
    anim.setDuration(ms)
    anim.setStartValue(0.0)
    anim.setEndValue(1.0)
    anim.setEasingCurve(QEasingCurve.Type.OutCubic)
    anim.finished.connect(lambda: _detach(widget, eff))
    if delay:
        QTimer.singleShot(delay, lambda: _start(anim))
    else:
        _start(anim)
    return anim


def fade_flip(widget, swap, ms=300):
    """Fade out, run `swap` (change the content), fade back in: a cheap card flip."""
    eff = QGraphicsOpacityEffect(widget)
    widget.setGraphicsEffect(eff)
    out = QPropertyAnimation(eff, b'opacity', widget)
    out.setDuration(ms // 2)
    out.setStartValue(1.0)
    out.setEndValue(0.0)
    out.setEasingCurve(QEasingCurve.Type.InQuad)
    inn = QPropertyAnimation(eff, b'opacity', widget)
    inn.setDuration(ms - ms // 2)
    inn.setStartValue(0.0)
    inn.setEndValue(1.0)
    inn.setEasingCurve(QEasingCurve.Type.OutCubic)
    seq = QSequentialAnimationGroup(widget)
    seq.addAnimation(out)
    seq.addPause(30)
    seq.addAnimation(inn)
    seq.finished.connect(lambda: _detach(widget, eff))
    seq.start()
    QTimer.singleShot(ms // 2, lambda: swap() if alive(widget) else None)
    return seq


def flash_css(widget, css, ms=260):
    """Temporarily swap a widget's stylesheet, then put the original one back.

    A second flash while one is pending keeps the first (original) stylesheet, so
    repeated flashes never restore an already-flashed look. Cancel with cancel_flash
    when a permanent repaint is about to land on the same widget.
    """
    if not hasattr(widget, '_fx_orig_css'):
        widget._fx_orig_css = widget.styleSheet()
    widget.setStyleSheet(css)
    t = getattr(widget, '_fx_restore', None)
    if t is not None:
        t.stop()
    t = QTimer(widget)
    t.setSingleShot(True)

    def restore():
        if not hasattr(widget, '_fx_orig_css'):
            return
        if widget.styleSheet() == css:               # still our flash: put the original back
            widget.setStyleSheet(widget._fx_orig_css)
        del widget._fx_orig_css                       # a permanent repaint won - never undo it
    t.timeout.connect(restore)
    t.start(ms)
    widget._fx_restore = t


def cancel_flash(widget):
    """Stop a pending css flash (call before a permanent repaint of that widget)."""
    t = getattr(widget, '_fx_restore', None)
    if t is not None:
        t.stop()
    if hasattr(widget, '_fx_orig_css'):
        widget.setStyleSheet(widget._fx_orig_css)
        del widget._fx_orig_css
