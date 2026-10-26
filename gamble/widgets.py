"""Small shared widgets and helpers."""
import math
import random

from PyQt6.QtCore import QPointF, QRectF, Qt, QTimer
from PyQt6.QtGui import QColor, QFont, QLinearGradient, QPainter, QPen, QPolygonF
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QWidget

from .i18n import tr
from .rules import RED          # noqa: F401  (card colours)

AC = Qt.AlignmentFlag.AlignCenter
CARD_SCALE = 1.0                       # D7: cards are drawn at this fraction of their normal size


class Button(QPushButton):
    """A button that never takes keyboard focus, so Space/Enter/letters always reach the shortcut handler."""

    def __init__(self, *args):
        super().__init__(*args)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)


class LineChart(QWidget):
    """Net worth over the days, with the goal as a dashed line."""
    GOLD = QColor('#f4c542')

    def __init__(self):
        super().__init__()
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
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(0, 0, 0, 70))
        p.drawRoundedRect(QRectF(self.rect()), 10, 10)
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


def paint_card(lbl, card, size=(68, 98)):
    """Draw `card` (a (text, suit) pair, or None for face-down) onto an existing card label.

    The box is re-sized here too, so the "Card size" setting reaches cards that were already
    dealt (and the Hi-Lo card, which is built once and only ever repainted)."""
    lbl.setFixedSize(*scaled(size))
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
    """card = (text, suit) or None for a face-down card."""
    lbl = QLabel()
    lbl.setFixedSize(*scaled(size))
    lbl.setAlignment(AC)
    return paint_card(lbl, card, size)


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
            self.parts.append([cx, cy, math.cos(ang) * speed, math.sin(ang) * speed - 4,
                               random.choice(self.COLORS), random.uniform(6, 11), 90 + random.randint(0, 40),
                               random.uniform(0, 360), random.uniform(-14, 14)])
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
        for x, y, _vx, _vy, color, size, life, angle, _spin in self.parts:
            c = QColor(color)
            c.setAlphaF(min(1.0, life / 30))
            painter.save()
            painter.translate(x + size / 2, y + size * 0.3)
            painter.rotate(angle)
            painter.fillRect(QRectF(-size / 2, -size * 0.3, size, size * 0.6), c)
            painter.restore()
