"""Reusable, purely-visual effects: particle bursts, shockwave rings, colour flashes,
floating numbers, cheap card flips, big-win banners, notification toasts and a start splash.

Nothing in here touches the rules, the engine or the game state - it only draws.
Decoration gets its own RNG (VRNG) so animation frames can never shift a game's result.
"""
import html
import math
import random

from PyQt6.QtCore import (QEasingCurve, QEvent, QParallelAnimationGroup, QPoint, QPropertyAnimation,
                          QSequentialAnimationGroup, QTimer, QVariantAnimation, Qt)
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


def shake(widget, ms=420, amp=10):
    """A damped left-right jolt of a top-level window: the 'something big just happened' beat.
    The window always lands back on the exact position it started from."""
    if not alive(widget):
        return None
    prev = getattr(widget, '_fx_shake', None)
    if prev is not None:                       # interrupted mid-flight: never adopt the offset
        try:
            prev.stop()
            prev.deleteLater()
        except RuntimeError:
            pass
        start = getattr(widget, '_fx_shake_start', widget.pos())
    else:
        start = widget.pos()
    anim = QVariantAnimation(widget)
    anim.setDuration(max(1, ms))
    anim.setStartValue(0.0)
    anim.setEndValue(1.0)

    def move(t):
        if not alive(widget):
            return
        falloff = (1.0 - t) ** 2               # hard at the start, nothing left at the end
        dx = amp * falloff * math.sin(t * math.pi * 10)
        dy = amp * 0.45 * falloff * math.cos(t * math.pi * 10)
        widget.move(start + QPoint(round(dx), round(dy)))

    def settle():
        if getattr(widget, '_fx_shake', None) is anim:
            widget._fx_shake = None            # only clear our own slot, never a newer shake's
        if alive(widget):
            widget.move(start)

    anim.valueChanged.connect(move)
    anim.finished.connect(settle)
    anim.finished.connect(anim.deleteLater)
    widget._fx_shake = anim
    widget._fx_shake_start = start
    anim.start()
    return anim


def banner(host, text, color='#f4c542', ms=1500, size=36, y_frac=0.30):
    """A big centred announcement (BIG WIN, JACKPOT) that pops in, holds and fades away."""
    if not alive(host):
        return None
    lbl = QLabel(host)
    lbl.setObjectName('fxBanner')
    lbl.setTextFormat(Qt.TextFormat.RichText)
    lbl.setText(f"<span style='color:{color}'>{html.escape(text)}</span>")
    lbl.setStyleSheet(f'background:rgba(8,10,16,0.88);border:3px solid {color};'
                      f'border-radius:18px;padding:16px 40px;font-size:{size}px;font-weight:800;')
    lbl.adjustSize()
    x, y = (host.width() - lbl.width()) // 2, round(host.height() * y_frac)
    lbl.move(x, y)
    lbl.show()
    lbl.raise_()
    end = lbl.geometry()
    eff = QGraphicsOpacityEffect(lbl)
    lbl.setGraphicsEffect(eff)
    small = QRectF(x + lbl.width() * 0.25, y + lbl.height() * 0.25,
                   max(8.0, lbl.width() * 0.5), max(8.0, lbl.height() * 0.5)).toRect()
    grow = QPropertyAnimation(lbl, b'geometry', lbl)
    grow.setStartValue(small)
    grow.setEndValue(end)
    grow.setDuration(260)
    grow.setEasingCurve(QEasingCurve.Type.OutBack)
    rise = QPropertyAnimation(lbl, b'pos', lbl)
    rise.setStartValue(end.topLeft())
    rise.setEndValue(end.topLeft() + QPoint(0, -26))
    rise.setDuration(420)
    rise.setEasingCurve(QEasingCurve.Type.OutCubic)
    fade = QPropertyAnimation(eff, b'opacity', lbl)
    fade.setStartValue(1.0)
    fade.setEndValue(0.0)
    fade.setDuration(420)
    fade.setEasingCurve(QEasingCurve.Type.InQuad)
    tail = QParallelAnimationGroup(lbl)
    tail.addAnimation(rise)
    tail.addAnimation(fade)
    seq = QSequentialAnimationGroup(lbl)
    seq.addAnimation(grow)
    seq.addPause(max(0, ms - 700))
    seq.addAnimation(tail)
    seq.finished.connect(lbl.deleteLater)
    seq.start()
    return lbl


def toast(host, title, body='', color='#f4c542', ms=3600, width=330):
    """A notification card in the top-right corner (level ups, achievements, records).
    Cards stack downwards, at most four are alive at once, and each removes itself."""
    if not alive(host):
        return None
    live = [t for t in getattr(host, '_fx_toasts', []) if alive(t)]
    while len(live) >= 4:                      # a burst of news must never bury the window
        live.pop(0).deleteLater()
    host._fx_toasts = live
    lbl = QLabel(host)
    lbl.setObjectName('fxToast')
    lbl.setTextFormat(Qt.TextFormat.RichText)
    lbl.setText(f"<span style='color:{color}'>{html.escape(title)}</span>"
                + (f"<br><span style='color:#cfd6e4'>{html.escape(body)}</span>" if body else ''))
    lbl.setWordWrap(True)
    lbl.setFixedWidth(width)
    lbl.setStyleSheet(f'background:rgba(12,15,22,0.95);color:#e8eaf0;border:1px solid #2a3248;'
                      f'border-left:5px solid {color};border-radius:10px;'
                      'padding:9px 12px;font-size:14px;')
    lbl.adjustSize()                           # wrapped to the fixed width
    x = max(0, host.width() - lbl.width() - 14)
    head = host.findChild(QLabel, 'appTitle')  # start below the header, never over its buttons
    top = head.y() + head.height() + 10 if head is not None and alive(head) else 14
    y = top + sum(t.height() + 8 for t in live)
    final = QPoint(x, y)
    lbl.move(x + 40, y)                        # slides in from just past the right edge
    lbl.show()
    lbl.raise_()
    eff = QGraphicsOpacityEffect(lbl)
    lbl.setGraphicsEffect(eff)
    eff.setOpacity(0.0)
    appear = QPropertyAnimation(lbl, b'pos', lbl)
    appear.setStartValue(QPoint(x + 40, y))
    appear.setEndValue(final)
    appear.setDuration(240)
    appear.setEasingCurve(QEasingCurve.Type.OutCubic)
    fade_in = QPropertyAnimation(eff, b'opacity', lbl)
    fade_in.setStartValue(0.0)
    fade_in.setEndValue(1.0)
    fade_in.setDuration(240)
    in_grp = QParallelAnimationGroup(lbl)
    in_grp.addAnimation(appear)
    in_grp.addAnimation(fade_in)
    leave = QPropertyAnimation(lbl, b'pos', lbl)
    leave.setStartValue(final)
    leave.setEndValue(final + QPoint(46, 0))
    leave.setDuration(320)
    leave.setEasingCurve(QEasingCurve.Type.InCubic)
    fade_out = QPropertyAnimation(eff, b'opacity', lbl)
    fade_out.setStartValue(1.0)
    fade_out.setEndValue(0.0)
    fade_out.setDuration(320)
    fade_out.setEasingCurve(QEasingCurve.Type.InQuad)
    out_grp = QParallelAnimationGroup(lbl)
    out_grp.addAnimation(leave)
    out_grp.addAnimation(fade_out)
    seq = QSequentialAnimationGroup(lbl)
    seq.addAnimation(in_grp)
    seq.addPause(ms)
    seq.addAnimation(out_grp)
    seq.finished.connect(lbl.deleteLater)
    seq.start()
    live.append(lbl)
    return lbl


def intro(host, title, sub='', ms=1100):
    """The start-screen splash: the logo fades in, holds, fades out. Clicks pass straight
    through it, so it can never block the window it covers."""
    if not alive(host):
        return None
    lbl = QLabel(host)
    lbl.setObjectName('fxIntro')
    lbl.setGeometry(host.rect())
    lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
    lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    lbl.setTextFormat(Qt.TextFormat.RichText)
    # HTML collapses runs of spaces, so the logo keeps its double space as non-breaking ones
    head = html.escape(title).replace('  ', '&nbsp;&nbsp;')
    body = f"<div style='color:#f4c542;font-size:54px;font-weight:800;'>{head}</div>"
    if sub:
        body += f"<div style='color:#9fb8ac;font-size:18px;font-weight:600;'>{html.escape(sub)}</div>"
    lbl.setText(body)
    lbl.setStyleSheet('background:rgba(8,10,16,0.93);')
    lbl.show()
    lbl.raise_()
    eff = QGraphicsOpacityEffect(lbl)
    lbl.setGraphicsEffect(eff)
    eff.setOpacity(0.0)
    inn = QPropertyAnimation(eff, b'opacity', lbl)
    inn.setStartValue(0.0)
    inn.setEndValue(1.0)
    inn.setDuration(260)
    inn.setEasingCurve(QEasingCurve.Type.OutCubic)
    out = QPropertyAnimation(eff, b'opacity', lbl)
    out.setStartValue(1.0)
    out.setEndValue(0.0)
    out.setDuration(380)
    out.setEasingCurve(QEasingCurve.Type.InQuad)
    seq = QSequentialAnimationGroup(lbl)
    seq.addAnimation(inn)
    seq.addPause(max(0, ms - 640))
    seq.addAnimation(out)
    seq.finished.connect(lbl.deleteLater)
    seq.start()
    return lbl
