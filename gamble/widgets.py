"""Small shared widgets and helpers."""
import math
import random

from PyQt6.QtCore import QPointF, QRectF, Qt, QTimer
from PyQt6.QtGui import (QColor, QFont, QIcon, QLinearGradient, QPainter, QPainterPath, QPen,
                         QPolygonF, QPixmap)
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QWidget

from . import sound
from .i18n import tr
from .rules import RANK_STR, RED          # noqa: F401  (card colours and rank labels)

AC = Qt.AlignmentFlag.AlignCenter
CARD_SCALE = 1.0                       # D7: cards are drawn at this fraction of their normal size


class Button(QPushButton):
    """A button that never takes keyboard focus, so Space/Enter/letters always reach the shortcut handler."""

    def __init__(self, *args):
        super().__init__(*args)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.clicked.connect(lambda: sound.play('click'))     # the soft tick of a chip landing


_ICON = None


def app_icon(size=256):
    """The game's icon: a gold casino chip with a G, drawn once at runtime (no image files).
    Used for the window, every dialog and - via tools/make_icon.py - the exe and installer."""
    global _ICON
    if _ICON is not None:
        return _ICON
    pm = QPixmap(size, size)
    pm.fill(QColor(0, 0, 0, 0))
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    m = size * 0.04
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor('#141821'))
    p.drawRoundedRect(QRectF(m, m, size - 2 * m, size - 2 * m), size * 0.18, size * 0.18)
    cx = cy = size / 2
    r = size * 0.34
    p.setPen(QPen(QColor('#f4c542'), size * 0.055))
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawEllipse(QPointF(cx, cy), r, r)
    p.setPen(QPen(QColor('#141821'), size * 0.05))            # the chip's six edge notches
    for i in range(6):
        a = math.radians(i * 60 + 30)
        p.drawLine(QPointF(cx + (r - size * 0.035) * math.cos(a), cy + (r - size * 0.035) * math.sin(a)),
                   QPointF(cx + (r + size * 0.035) * math.cos(a), cy + (r + size * 0.035) * math.sin(a)))
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor('#1c2230'))
    p.drawEllipse(QPointF(cx, cy), r * 0.66, r * 0.66)
    p.setPen(QColor('#f4c542'))
    font = QFont()
    font.setPixelSize(int(size * 0.30))
    font.setBold(True)
    p.setFont(font)
    p.drawText(QRectF(0, 0, size, size), AC, 'G')
    p.end()
    icon = QIcon()
    for s in (16, 24, 32, 48, 64, 128, 256):
        icon.addPixmap(pm.scaled(s, s, Qt.AspectRatioMode.KeepAspectRatio,
                                 Qt.TransformationMode.SmoothTransformation))
    _ICON = icon
    return icon


class LineChart(QWidget):
    """Net worth over the days, with the goal as a dashed line."""
    GOLD = QColor('#f4c542')

    def __init__(self):
        super().__init__()
        self.setObjectName('netChart')           # D17: a themed panel instead of a painted black box
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground)
        self.points = []
        self.goal = None
        self.setMinimumHeight(200)

    def set_data(self, points, goal=None):
        self.points = list(points)
        self.goal = goal
        self.update()

    @staticmethod
    def short(v):
        a = abs(v)
        if a >= 1_000_000:
            return f'{v / 1_000_000:.1f}M'
        if a >= 10_000:
            return f'{v / 1000:.0f}k'
        if a >= 1000:
            return f'{v / 1000:.1f}k'
        return f'{v:.0f}'

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        font = QFont(p.font())
        font.setPointSize(9)
        p.setFont(font)
        w, h = self.width(), self.height()
        ml, mr, mt, mb = 56, 16, 14, 26
        pw, ph = w - ml - mr, h - mt - mb
        muted = QColor('#8b93a8')
        if len(self.points) < 2:
            p.setPen(muted)
            p.drawText(QRectF(self.rect()), AC, 'Play a few days to see your net worth chart.')
            return
        xs = [d for d, _ in self.points]
        ys = [v for _, v in self.points]
        ymin, ymax = min(0, min(ys)), max(ys)
        if self.goal and ymax >= self.goal * 0.3:
            ymax = max(ymax, self.goal)
        if ymax <= ymin:
            ymax = ymin + 1
        ymax += (ymax - ymin) * 0.06
        x0, x1 = xs[0], max(xs[-1], xs[0] + 1)

        def X(d):
            return ml + (d - x0) / (x1 - x0) * pw

        def Y(v):
            return mt + ph - (v - ymin) / (ymax - ymin) * ph

        for i in range(5):                                   # grid and y labels
            v = ymin + (ymax - ymin) * i / 4
            y = Y(v)
            p.setPen(QPen(QColor(255, 255, 255, 28), 1))
            p.drawLine(QPointF(ml, y), QPointF(w - mr, y))
            p.setPen(muted)
            p.drawText(QRectF(0, y - 9, ml - 6, 18), Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                       self.short(v))
        p.setPen(muted)
        p.drawText(QRectF(ml, h - mb + 4, 80, 18), Qt.AlignmentFlag.AlignLeft, f'day {x0}')
        p.drawText(QRectF(w - mr - 80, h - mb + 4, 80, 18), Qt.AlignmentFlag.AlignRight, f'day {xs[-1]}')
        if self.goal and ymax >= self.goal:                  # goal line
            y = Y(self.goal)
            p.setPen(QPen(QColor('#d4a017'), 1.5, Qt.PenStyle.DashLine))
            p.drawLine(QPointF(ml, y), QPointF(w - mr, y))
            p.drawText(QRectF(ml + 6, y - 18, 120, 16), Qt.AlignmentFlag.AlignLeft, 'goal')
        pts = [QPointF(X(d), Y(v)) for d, v in self.points]
        base_y = Y(max(ymin, 0))
        area = QPolygonF([QPointF(pts[0].x(), base_y)] + pts + [QPointF(pts[-1].x(), base_y)])
        grad = QLinearGradient(QPointF(0, base_y), QPointF(0, mt))
        top = QColor(self.GOLD)
        top.setAlpha(110)
        bottom = QColor(self.GOLD)
        bottom.setAlpha(8)
        grad.setColorAt(0.0, top)
        grad.setColorAt(1.0, bottom)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(grad)
        p.drawPolygon(area)
        glow = QColor(self.GOLD)
        glow.setAlpha(60)
        p.setPen(QPen(glow, 7, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        p.drawPolyline(QPolygonF(pts))
        p.setPen(QPen(self.GOLD, 2.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawPolyline(QPolygonF(pts))
        p.setPen(QPen(QColor(255, 255, 255, 160), 1.5))
        p.setBrush(self.GOLD)
        p.drawEllipse(pts[-1], 4.5, 4.5)


def clear_layout(layout):
    while layout.count():
        item = layout.takeAt(0)
        if item.widget():
            item.widget().hide()                    # gone now, not at the next event-loop turn
            item.widget().deleteLater()
        elif item.layout():
            clear_layout(item.layout())


def set_card_scale(scale):
    """D7: how large the playing cards are drawn (1.0 = the classic 68x98)."""
    global CARD_SCALE
    CARD_SCALE = max(0.5, min(2.0, float(scale)))


def scaled(size=(68, 98)):
    return (max(36, round(size[0] * CARD_SCALE)), max(52, round(size[1] * CARD_SCALE)))


def draw_card(p, w, h, card, checked=False):
    """D17: one painter for every playing card in the game. `card` is a (rank, suit) pair or
    None for face-down; `checked` gives the gold frame of a poker card marked for a change.

    A card is a white gradient body with a drop shadow tucked under its bottom-right corner,
    a hairline inside the border, the rank and suit centred and a tiny pip in each corner.
    The back is navy with a white frame, a clipped diagonal lattice and a star emblem.
    Everything is drawn in local coordinates - the caller only decides where the card sits."""
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    r = max(6, round(min(w, h) * 0.10))
    body = QRectF(0, 0, w - 3, h - 4)                # the shadow gets the bottom-right strip
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor(0, 0, 0, 90))
    p.drawRoundedRect(body.translated(3, 4), r, r)
    if card is None:
        grad = QLinearGradient(0, 0, w, h)
        grad.setColorAt(0.0, QColor('#2f4d8f'))
        grad.setColorAt(1.0, QColor('#1c2f5e'))
        p.setBrush(grad)
        p.setPen(QPen(QColor('#e8eaf0'), max(1, round(2 * w / 68))))
        p.drawRoundedRect(body, r, r)
        inner = body.adjusted(5, 5, -5, -5)
        p.save()                                      # the lattice, clipped inside the frame
        path = QPainterPath()
        path.addRoundedRect(inner, r * 0.7, r * 0.7)
        p.setClipPath(path)
        p.setPen(QPen(QColor(255, 255, 255, 26), 1))
        step = max(7, round(w / 9))
        for x in range(-h, w + h, step):
            p.drawLine(QPointF(x, h), QPointF(x + h, 0))
            p.drawLine(QPointF(x, 0), QPointF(x + h, h))
        p.restore()
        p.setPen(QPen(QColor(232, 234, 240, 170), 1))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(inner, r * 0.7, r * 0.7)
        cx, cy = body.center().x(), body.center().y()  # the star emblem in a ring
        rad = min(w, h) * 0.20
        p.setPen(QPen(QColor('#8fb0ff'), max(1.5, w / 40)))
        p.setBrush(QColor(255, 255, 255, 20))
        p.drawEllipse(QPointF(cx, cy), rad, rad)
        font = QFont(p.font())
        font.setPixelSize(max(12, round(rad * 1.05)))
        font.setBold(True)
        p.setFont(font)
        p.setPen(QColor('#dce8ff'))
        p.drawText(QRectF(cx - rad, cy - rad, rad * 2, rad * 2), AC, '★')
        return
    text, suit = card
    rank = RANK_STR.get(text, text)                   # poker decks carry ints, the rest strings
    color = QColor('#c62828') if suit in RED else QColor('#111111')
    scale = w / 68
    grad = QLinearGradient(0, 0, 0, h)
    grad.setColorAt(0.0, QColor('#ffffff'))
    grad.setColorAt(1.0, QColor('#eceff4'))
    p.setBrush(grad)
    p.setPen(QPen(QColor('#f4c542') if checked else QColor('#cfcfcf'),
                  max(2, round(3 * scale)) if checked else max(1, round(scale))))
    p.drawRoundedRect(body, r, r)
    p.setPen(QPen(QColor(255, 255, 255, 150), 1))     # the inner hairline
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawRoundedRect(body.adjusted(1.5, 1.5, -1.5, -1.5), r - 1, r - 1)
    font = QFont(p.font())                            # the rank and the suit, centred
    font.setPixelSize(max(10, round(22 * scale)))
    font.setBold(True)
    p.setFont(font)
    p.setPen(color)
    p.drawText(body, Qt.AlignmentFlag.AlignCenter, f'{rank}\n{suit}')
    fs_pip = max(7, round(9 * scale))                 # a tiny pip in each corner
    pip = QFont(p.font())
    pip.setPixelSize(fs_pip)
    p.setFont(pip)
    m = max(3, round(4 * scale))
    p.drawText(QRectF(body.x() + m, body.y() + m, body.width() / 2, fs_pip + 2),
               Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop, str(suit))
    p.save()
    p.translate(body.x() + body.width() - m, body.y() + body.height() - m)
    p.rotate(180)
    p.drawText(QRectF(0, 0, body.width() / 2, fs_pip + 2),
               Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop, str(suit))
    p.restore()


class CardFace(QLabel):
    """D17: a card label that paints itself with draw_card instead of faking the whole card
    with a stylesheet."""

    def __init__(self, card=None, size=(68, 98)):
        super().__init__()
        self.setAlignment(AC)
        self._card = 'unset'
        self.set_card(card, size)

    def set_card(self, card, size=(68, 98)):
        self.setFixedSize(*scaled(size))
        self._card = card                        # so callers can skip repainting an unchanged card
        self.update()

    def paintEvent(self, _event):
        p = QPainter(self)
        draw_card(p, self.width(), self.height(), self._card)
        p.end()


def paint_card(lbl, card, size=(68, 98)):
    """Draw `card` (a (text, suit) pair, or None for face-down) onto an existing card label.

    The box is re-sized here too, so the "Card size" setting reaches cards that were already
    dealt (and the Hi-Lo card, which is built once and only ever repainted)."""
    lbl.setFixedSize(*scaled(size))
    if isinstance(lbl, CardFace):               # D17: self-painting, no stylesheet involved
        lbl.set_card(card, size)
        return lbl
    w, _h = scaled(size)
    scale = w / 68
    fs = max(10, round(22 * scale))
    fs_back = max(14, round(30 * scale))
    edge = max(6, round(9 * scale))
    bw = max(1, round(2 * scale))
    if card is None:
        lbl.setText('★')
        lbl.setStyleSheet(
            'background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #2f4d8f,stop:1 #1c2f5e);'
            f'color:#8fb0ff;border:{bw}px solid #e8eaf0;border-radius:{edge}px;font-size:{fs_back}px;')
    else:
        text, suit = card
        color = '#c62828' if suit in RED else '#111111'
        lbl.setText(f'{text}\n{suit}')
        lbl.setStyleSheet(
            f'background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #ffffff,stop:1 #eceff4);'
            f'color:{color};border:{bw}px solid #cfcfcf;border-radius:{edge}px;'
            f'font-size:{fs}px;font-weight:700;')
    lbl._card = card                        # so callers can skip repainting an unchanged card
    return lbl


def make_card(card, size=(68, 98)):
    """card = (text, suit) or None for a face-down card. D17: a self-painting CardFace."""
    return CardFace(card, size)


class PokerCard(Button):
    """D17: the poker hand's own cards as buttons - the same draw_card as every other card on
    the table, with a gold frame on the ones marked for a change."""

    def __init__(self, card=None, size=(76, 108)):
        super().__init__()
        self._card = 'unset'
        self.set_card(card, size)

    def set_card(self, card, size=(76, 108)):
        self.setFixedSize(*scaled(size))
        self._card = card
        self.update()

    def paintEvent(self, _event):
        p = QPainter(self)
        draw_card(p, self.width(), self.height(), self._card, checked=self.isChecked())
        p.end()


class CardRow(QWidget):
    def __init__(self):
        super().__init__()
        self.lay = QHBoxLayout(self)
        self.lay.setContentsMargins(0, 0, 0, 0)
        self.lay.setSpacing(8)
        self.lay.setAlignment(AC)

    def set_cards(self, cards):
        """Show `cards`, reusing the labels from the previous deal: unchanged cards stay exactly
        where they are instead of being destroyed and rebuilt, which made the whole row flicker."""
        while self.lay.count() < len(cards):
            self.lay.addWidget(make_card(None))
        while self.lay.count() > len(cards):
            w = self.lay.takeAt(self.lay.count() - 1).widget()
            if w is not None:
                w.hide()                    # gone now, not lingering for one more frame
                w.deleteLater()
        for i, c in enumerate(cards):
            w = self.lay.itemAt(i).widget()
            if w is not None and getattr(w, '_card', None) != c:
                paint_card(w, c)


def centered(text, name=None):
    lbl = QLabel(text)
    lbl.setAlignment(AC)
    lbl.setWordWrap(True)
    if name:
        lbl.setObjectName(name)
    return lbl


def section(text):
    lbl = QLabel(text)
    lbl.setObjectName('section')
    return lbl


def page_title(text):
    t = QLabel(text)
    t.setObjectName('gameTitle')
    return t


def back_button(app):
    b = Button(tr('← Back to lobby'))
    b.clicked.connect(app.show_lobby)
    return b


def paint(btn, bg, fg, border):
    btn.setStyleSheet(f'QPushButton, QPushButton:disabled {{ background:{bg}; color:{fg}; '
                      f'border:2px solid {border}; border-radius:6px; padding:0; font-weight:700; }}')


class Confetti(QWidget):
    """A short confetti burst drawn over the whole window. Lets clicks through."""
    COLORS = ['#f4c542', '#4cc38a', '#ff6b6b', '#6c8cff', '#e8eaf0', '#b06ee0']

    def __init__(self, parent):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.parts = []
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.step)
        self.hide()

    def burst(self, n=90):
        host = self.parentWidget()
        self.setGeometry(0, 0, host.width(), host.height())
        self.raise_()
        self.show()
        cx, cy = self.width() / 2, self.height() * 0.3
        for _ in range(n):
            ang, speed = random.uniform(0, 2 * math.pi), random.uniform(3, 11)
            # D17: a 10th field - the shape this piece is: 0 streamer, 1 dot, 2 chip
            shape = random.choices((0, 1, 2), weights=(45, 30, 25))[0]
            self.parts.append([cx, cy, math.cos(ang) * speed, math.sin(ang) * speed - 4,
                               random.choice(self.COLORS), random.uniform(6, 11), 90 + random.randint(0, 40),
                               random.uniform(0, 360), random.uniform(-14, 14), shape])
        if not self.timer.isActive():
            self.timer.start(16)

    def step(self):
        for p in self.parts:
            p[0] += p[2]
            p[1] += p[3]
            p[3] += 0.3
            p[2] *= 0.99
            p[6] -= 1
            p[7] += p[8]
        self.parts = [p for p in self.parts if p[6] > 0 and p[1] < self.height() + 20]
        if not self.parts:
            self.timer.stop()
            self.hide()
        self.update()

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        for x, y, _vx, _vy, color, size, life, angle, _spin, shape in self.parts:
            c = QColor(color)
            c.setAlphaF(min(1.0, life / 30))
            painter.save()
            painter.translate(x + size / 2, y + size * 0.3)
            painter.rotate(angle)
            if shape == 1:                            # a dot
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(c)
                painter.drawEllipse(QPointF(0, 0), size * 0.42, size * 0.42)
            elif shape == 2:                          # a casino chip: a disc with a white ring
                painter.setPen(QPen(QColor(255, 255, 255, max(40, int(c.alpha() * 0.7))),
                                    max(1, size * 0.12)))
                painter.setBrush(c)
                painter.drawEllipse(QPointF(0, 0), size * 0.45, size * 0.45)
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawEllipse(QPointF(0, 0), size * 0.2, size * 0.2)
            else:                                     # the classic streamer
                painter.fillRect(QRectF(-size / 2, -size * 0.3, size, size * 0.6), c)
            painter.restore()


class Watermark(QWidget):
    """D17: a field of very faint, oversized suit glyphs across the table felt - casino-table
    texture drawn behind everything. Deaf to the mouse; only exists with effects on."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        fs = max(40, min(150, self.height() // 3))
        font = QFont(p.font())
        font.setPixelSize(fs)
        p.setFont(font)
        w, h = self.width(), self.height()
        step_x, step_y = fs * 2.0, fs * 2.2
        cols = max(1, (w - fs) // int(step_x) + 1)
        rows = max(1, (h - fs) // int(step_y) + 1)
        ox = (w - (cols - 1) * step_x) / 2
        oy = (h - (rows - 1) * step_y) / 2
        suits = (('♠', QColor(255, 255, 255, 22)), ('♣', QColor(255, 255, 255, 22)),
                 ('♥', QColor(255, 110, 110, 30)), ('♦', QColor(255, 110, 110, 30)))
        for r in range(rows):
            for c in range(cols):
                glyph, color = suits[(r * 2 + c) % 4]
                p.setPen(color)
                x, y = ox + c * step_x, oy + r * step_y
                p.drawText(QRectF(x - step_x / 2, y - step_y / 2, step_x, step_y), AC, glyph)
        p.end()
