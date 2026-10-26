"""Base class of every game page: layout, result banner, animation helpers and keyboard bindings."""
import traceback

from PyQt6.QtCore import QEasingCurve, QPoint, QPropertyAnimation, Qt, QTimer
from PyQt6.QtWidgets import QFrame, QGraphicsOpacityEffect, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from ..config import GAME_NAMES
from ..fx import FxOverlay, flash_css, float_text
from ..widgets import Button, centered

K = Qt.Key


def digit_key(n):
    return getattr(K, f'Key_{n}')


class BaseGame(QWidget):
    key = ''
    title = ''

    def __init__(self, app, bet):
        super().__init__()
        self.app, self.bet = app, bet
        self.in_progress = False
        self.keys = {}            # Qt key -> [button or callable]; the window dispatches key presses here
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(10)
        head = QHBoxLayout()
        t = QLabel(self.title)
        t.setObjectName('gameTitle')
        b = QLabel(f'Bet: {bet:,} TL')
        b.setObjectName('betTag')
        head.addWidget(t)
        head.addStretch()
        head.addWidget(b)
        outer.addLayout(head)
        self.felt = QFrame()
        self.felt.setObjectName('felt')
        self.fx = FxOverlay(self.felt)          # particles / flashes live on the table felt
        self.body = QVBoxLayout(self.felt)
        self.body.setContentsMargins(20, 20, 20, 20)
        self.body.setSpacing(12)
        outer.addWidget(self.felt, 1)
        self.result = centered('', 'result')
        outer.addWidget(self.result)
        foot = QHBoxLayout()
        self.back_btn = Button('← Back to lobby  [Esc]')
        self.back_btn.clicked.connect(self.app.show_lobby)
        self.again_btn = Button('Play again  [Space]')
        self.again_btn.setObjectName('primary')
        self.again_btn.hide()
        self.again_btn.clicked.connect(lambda: self.app.play_again(self.key, self.bet))
        foot.addWidget(self.back_btn)
        foot.addStretch()
        foot.addWidget(self.again_btn)
        outer.addLayout(foot)
        self.build()
        for k in (K.Key_Return, K.Key_Enter, K.Key_Space):     # last in line: start the next round
            self.bind(k, self.again_btn)

    @property
    def rng(self):
        return self.app.engine.rng

    @property
    def edge(self):
        """House edge of the edge-based games (Crash / Mines / Hi-Lo) for this run's difficulty."""
        return self.app.state.diff.get('edge', 0.08)

    def build(self):
        raise NotImplementedError

    def bind(self, key, target):
        self.keys.setdefault(key, []).append(target)

    def lock(self, on=True):
        self.in_progress = on
        self.back_btn.setEnabled(not on)

    def after(self, ms, fn):
        t = QTimer(self)
        t.setSingleShot(True)
        t.timeout.connect(fn)
        t.start(int(ms * self.app.anim_factor()))

    def animate(self, steps, interval, tick, done):
        factor = self.app.anim_factor()
        if factor == 0:                      # animations off: jump straight to the result
            self.after(0, lambda: self.safe_done(done))
            return
        state = {'n': 0}
        t = QTimer(self)

        def step():
            state['n'] += 1
            if state['n'] >= steps:
                t.stop()
                t.deleteLater()
                self.safe_done(done)
            else:
                tick(state['n'])
        t.timeout.connect(step)
        t.start(max(10, int(interval * factor)))

    def safe_done(self, done):
        """Run a finished round's final step. If it ever throws, the page must still not freeze:
        report it and put the controls back instead of leaving every button dead."""
        try:
            done()
        except Exception:                    # noqa: BLE001 - the UI has to stay usable
            traceback.print_exc()
            self.lock(False)
            self.result.setStyleSheet('color:#ff6b6b;')
            self.result.setText('Something went wrong finishing this round (see the console). '
                                'Press Esc or Space to continue.')
            self.again_btn.show()

    def animate_result(self):
        """Fade the result banner in so a finished round feels less abrupt."""
        if not self.app.settings.effects or self.app.anim_factor() == 0:
            return
        effect = QGraphicsOpacityEffect(self.result)
        self.result.setGraphicsEffect(effect)
        anim = QPropertyAnimation(effect, b'opacity', self.result)
        anim.setDuration(int(320 * self.app.anim_factor()))
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim.finished.connect(lambda: self.result.setGraphicsEffect(None))
        anim.start()

    # ---- purely visual helpers (they never touch the rules or the state)
    def effects_on(self):
        return self.app.settings.effects

    def fx_point(self, widget, rx=0.5, ry=0.5):
        """A point inside `widget` (0..1 fractions), in felt coordinates."""
        p = widget.mapTo(self.felt, QPoint(round(widget.width() * rx), round(widget.height() * ry)))
        return p.x(), p.y()

    def burst_at(self, x, y, n=18, colors=None, speed=(2.0, 7.5), gravity=0.28, size=(3, 7), life=(28, 52)):
        if self.effects_on():
            self.fx.burst(x, y, n, colors, speed, gravity, size, life)

    def burst_on(self, widget, rx=0.5, ry=0.5, **kw):
        x, y = self.fx_point(widget, rx, ry)
        self.burst_at(x, y, **kw)

    def ring_on(self, widget, rx=0.5, ry=0.5, color='#f4c542', r1=70, width=3, ms=320):
        if self.effects_on():
            x, y = self.fx_point(widget, rx, ry)
            self.fx.ring(x, y, r1=r1, color=color, width=width, ms=ms)

    def fx_flash(self, color, alpha=60, ms=320):
        if self.effects_on():
            self.fx.flash(color, alpha, ms)

    def float_gain(self, widget, text, color='#4cc38a', size=20, rx=0.5, ry=0.4):
        if self.effects_on():
            x, y = self.fx_point(widget, rx, ry)
            float_text(self.felt, QPoint(x, y), text, color, size)

    def pulse(self, widget, css, ms=240):
        if self.effects_on() and self.app.anim_factor() > 0:
            flash_css(widget, css, ms)

    def finish_with(self, outcome):
        """outcome = (delta, win, text, tags) straight from a rules.settle_* function."""
        delta, win, text, tags = outcome
        self.finish(delta, win, text, tags)

    def finish(self, delta, win, text, tags=()):
        eng = self.app.engine
        delta, insured, notes = eng.apply_item_modifiers(delta, win, self.bet)
        self.lock(False)
        kind = 'win' if win is True else 'loss' if win is False else 'info'
        color = {'win': '#4cc38a', 'loss': '#ff6b6b', 'info': '#e8eaf0'}[kind]
        amount = f'+{delta:,} TL' if delta > 0 else (f'{delta:,} TL' if delta < 0 else 'bet returned')
        if notes:
            text += ' ' + '. '.join(notes) + '.'
        self.result.setStyleSheet(f'color:{color};')
        if kind != 'info':
            self.felt.setStyleSheet(f'QFrame#felt {{ border:3px solid {color}; }}')
        self.result.setText(f'{text}  ({amount})')
        self.animate_result()
        if win is True:                                   # a little celebration on the felt
            self.burst_on(self.result, n=12, colors=['#f4c542', '#ffe9a3', '#4cc38a'],
                          speed=(1.5, 4.5), gravity=0.22, size=(3, 6))
        elif win is False:
            self.fx_flash('#ff6b6b', 22, 260)
        eng.log(f'{GAME_NAMES[self.key]}: {text} ({amount})', kind)
        self.app.finish_round(self.key, delta, win, self.bet, tags, insured)
        s = eng.state
        if s.balance >= 1 and s.mental > 0:
            self.again_btn.show()
