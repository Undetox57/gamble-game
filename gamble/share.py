"""D10: a shareable result card - one PNG with the run's headline numbers.

The card is rendered with QPainter (no image assets), saved next to the save files and copied
to the clipboard, so the player can post it anywhere. Everything on the card goes through
tr(), so the card speaks the interface language.
"""
import os
import time

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QBrush, QColor, QFont, QImage, QLinearGradient, QPainter, QPen

from . import config
from .i18n import tr, txf

W, H = 1200, 630                       # the usual social preview size

GOLD, INK, WHITE, MUTED = '#f4c542', '#141821', '#e8eaf0', '#8f97ad'
GREEN, RED = '#4cc38a', '#ff6b6b'


def render(state, session=None):
    """Build the card image (1200x630) for a run, optionally with the current session line."""
    img = QImage(W, H, QImage.Format.Format_RGB32)
    grad = QLinearGradient(0, 0, 0, H)
    grad.setColorAt(0.0, QColor(INK))
    grad.setColorAt(1.0, QColor('#10131b'))
    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    p.fillRect(0, 0, W, H, QBrush(grad))
    p.setPen(QPen(QColor(GOLD), 3))
    p.drawRoundedRect(QRectF(14, 14, W - 28, H - 28), 18, 18)

    big = lambda size, weight=700: p.setFont(_font(size, weight))   # noqa: E731
    muted = QColor(MUTED)
    gold = QColor(GOLD)

    # ---- header
    big(34)
    p.setPen(gold)
    p.drawText(QPointF(52, 84), tr('🎰  GAMBLE GAME'))
    big(18, 400)
    p.setPen(muted)
    stamp = time.strftime('%Y-%m-%d %H:%M')
    p.drawText(QRectF(52, 46, W - 104, 30), Qt.AlignmentFlag.AlignRight, stamp)

    # ---- the headline number
    big(20, 600)
    p.setPen(muted)
    p.drawText(QPointF(52, 148), tr('NET WORTH'))
    big(76, 800)
    p.setPen(gold)
    p.drawText(QPointF(48, 218), f'{state.net_worth:,} TL')

    # ---- four stat blocks
    blocks = ((tr('DAY'), str(state.day)),
              (tr('LEVEL'), str(state.level)),
              (tr('MENTAL HEALTH'), f'{state.mental}/100'),
              (tr('GOAL'), f'{min(100, state.net_worth * 100 // max(1, state.goal))}%'))
    x = 52.0
    for caption, value in blocks:
        big(16, 600)
        p.setPen(muted)
        p.drawText(QPointF(x, 300), caption)
        big(30, 700)
        p.setPen(QColor(WHITE))
        p.drawText(QPointF(x, 342), value)
        x += 280

    # ---- the session strip
    if session:
        p.setPen(QPen(QColor('#2a3248'), 1))
        p.drawLine(QPointF(52, 388), QPointF(W - 52, 388))
        big(22, 600)
        p.setPen(QColor(WHITE))
        p.drawText(QPointF(52, 432), tr('SESSION') + '  •  ' + txf('{g} games', g=session['games'])
                   + '  •  ' + txf('{w} won, {l} lost', w=session['wins'],
                                   l=max(0, session['games'] - session['wins'])))
        delta = state.net_worth - session.get('net0', state.net_worth)
        p.setPen(QColor(GREEN) if delta >= 0 else QColor(RED))
        big(24, 700)
        p.drawText(QPointF(52, 474), f'{delta:+,} TL  ' + tr('this session'))

    # ---- footer
    big(18, 500)
    p.setPen(muted)
    p.drawText(QRectF(52, H - 66, W - 104, 30), Qt.AlignmentFlag.AlignLeft, tr('Result card'))
    p.drawText(QRectF(52, H - 66, W - 104, 30), Qt.AlignmentFlag.AlignRight,
               'undetox57.itch.io/gamble-game')
    p.end()
    return img


def _font(size, weight=400):
    f = QFont('Segoe UI')
    f.setPixelSize(size)
    f.setWeight(weight)
    return f


def save(img, state):
    """Write the card next to the save files and hand back its path."""
    folder = getattr(config, 'SHARE_DIR', None) or os.path.join(config.BASE_DIR, 'share')
    os.makedirs(folder, exist_ok=True)
    stamp = time.strftime('%Y%m%d-%H%M%S') + f'-{int(time.time() * 1000) % 1000:03d}'
    path = os.path.join(folder, f'result-card_day{state.day}_{state.difficulty}_{stamp}.png')
    img.save(path, 'PNG')
    return path


def share(win):
    """Render the card for the current run, save it and put it on the clipboard."""
    from PyQt6.QtWidgets import QApplication
    img = render(win.state, getattr(win, 'session', None))
    path = save(img, win.state)
    QApplication.clipboard().setImage(img)
    return path
