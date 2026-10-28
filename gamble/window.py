"""The main window: layout, navigation, keyboard shortcuts and the small visual effects.
All game rules live in engine.py; this file only shows them and asks the engine to act."""
import html
import os
import time

from PyQt6.QtCore import (QEasingCurve, QParallelAnimationGroup, QPoint, QPropertyAnimation, QRect,
                          QSequentialAnimationGroup, QVariant, QVariantAnimation, Qt, QTimer)
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWidgets import (QAbstractButton, QApplication, QFrame, QGraphicsOpacityEffect, QGridLayout,
                             QHBoxLayout, QLabel, QMainWindow, QMessageBox, QProgressBar, QScrollArea, QSpinBox,
                             QStackedWidget, QTextEdit, QVBoxLayout, QWidget)

from . import config, share, sound
from .config import (CATEGORIES, CLEAN_STREAKS_FOR_ENDING, CLEAN_TARGET, GAME_HOTKEYS, GAME_NAMES, GAME_SUBTITLES,
                     ITEM_BY_KEY, LEVEL_EXP, LOBBY_ORDER, TOURNAMENT_BONUS_RATE, TOURNAMENT_DAYS,
                     TOURNAMENT_ENTRY, TOURNAMENT_SPRINT_BONUS_CAP, TOURNAMENT_SPRINT_BONUS_RATE,
                     TOURNAMENT_SPRINT_DAYS, TOURNAMENT_SPRINT_ENTRY, UNLOCK)
from .dialogs import EndingDialog, EventDialog, KeybindDialog, NewGameDialog, SettingsDialog, key_from_name
from .engine import Engine
from .fx import alive
from .games import GAMES
from .i18n import current, set_lang, tr, txf
from .pages import AchievementsPage, BankPage, HelpPage, JobsPage, ShopPage, StatsPage, TrophyPage
from .style import ANIM_SPEEDS, CARD_SIZES, CATEGORY_ACCENTS, GAME_ICONS, TEXT_SCALES, Settings, build_style
from .widgets import Button, Confetti, section, set_card_scale

K = Qt.Key
DIGITS = [K.Key_1, K.Key_2, K.Key_3, K.Key_4, K.Key_5, K.Key_6, K.Key_7, K.Key_8, K.Key_9, K.Key_0]


class MainWindow(QMainWindow):
    def __init__(self, autostart=True):
        super().__init__()
        self.setWindowTitle('Gamble Game')
        self.resize(1220, 860)
        self.settings = Settings()
        self.settings.load()
        set_lang(self.settings.lang)                  # D9: everything built below uses this language
        self.engine = Engine()
        self.state, self.meta = self.engine.state, self.engine.meta
        self.meta.load()
        self.engine.log_fn = self.log
        self.engine.celebrate_fn = self.celebrate
        self.game_page = None
        self._last_balance = None
        self._ticker = None                        # D2: the wallet number counts up instead of jumping
        self.session = {'start': time.time(), 'games': 0, 'wins': 0, 'best': 0, 'net0': 0}
        self.build_ui()

        self.log('Welcome to the Gamble Game!', 'warn')
        self.fresh_install = not os.path.exists(config.SAVE_FILE)
        err = self.state.load()
        if err:
            self.log(err, 'loss')
        self.session['net0'] = self.state.net_worth     # D1: the session starts here
        self.stack.setCurrentWidget(self.lobby)
        self.refresh()
        if autostart:
            QTimer.singleShot(0, self.startup)

    # ---- building the UI
    def build_ui(self):
        """(Re)build every widget in the current language. Called once at startup and again
        whenever the player switches the interface language in Settings (D9)."""
        for sc in getattr(self, '_shortcuts', []):
            sc.deleteLater()                          # the old window shortcuts go with the old UI
        self._shortcuts = []
        self.game_page = None
        self._last_balance = None
        self._ticker = None
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(16, 12, 16, 12)
        root.setSpacing(10)
        head = QHBoxLayout()
        title = QLabel(tr('🎰  GAMBLE GAME'))
        title.setObjectName('appTitle')
        head.addWidget(title)
        head.addStretch()
        self.fs_btn = Button()
        self.fs_btn.setObjectName('headBtn')
        self.fs_btn.clicked.connect(self.toggle_fullscreen)
        settings_btn = Button(tr('⚙  Settings'))
        settings_btn.setObjectName('headBtn')
        settings_btn.clicked.connect(self.open_settings)
        head.addWidget(self.fs_btn)
        head.addWidget(settings_btn)
        root.addLayout(head)
        hairline = QFrame()
        hairline.setObjectName('hairline')
        hairline.setFixedHeight(2)
        root.addWidget(hairline)
        mid = QHBoxLayout()
        mid.setSpacing(14)
        mid.addWidget(self.build_side())
        self.stack = QStackedWidget()
        self.lobby = self.build_lobby()
        self.bank_page, self.stats_page = BankPage(self), StatsPage(self)
        self.jobs_page, self.ach_page = JobsPage(self), AchievementsPage(self)
        self.shop_page, self.help_page = ShopPage(self), HelpPage(self)
        self.trophy_page = TrophyPage(self)                  # D11: the trophy case
        self.page_wrap = {}
        for w in (self.lobby, self.bank_page, self.stats_page, self.jobs_page, self.ach_page, self.shop_page,
                  self.help_page, self.trophy_page):
            wrap = w if w is self.lobby else self.scrollable(w)
            self.page_wrap[w] = wrap
            self.stack.addWidget(wrap)
        mid.addWidget(self.stack, 1)
        root.addLayout(mid, 1)
        self.logbox = QTextEdit()
        self.logbox.setReadOnly(True)
        self.logbox.setFixedHeight(110)
        root.addWidget(self.logbox)
        self.confetti = Confetti(central)
        for seq, fn in (('F11', self.toggle_fullscreen), ('F1', self.show_help), ('Ctrl+Q', self.close)):
            sc = QShortcut(QKeySequence(seq), self)
            sc.activated.connect(fn)
            self._shortcuts.append(sc)
        self.apply_settings(initial=True)

    # ---- startup
    def startup(self):
        if self.fresh_install:
            self.ask_new_game(first_time=True)
        elif not self.handle_endings():
            self.process_events()

    def ask_new_game(self, first_time=False):
        dlg = NewGameDialog(self, first_time)
        dlg.exec()
        self.engine.new_game(dlg.choice)
        self._last_balance = None
        self.session['net0'] = self.state.net_worth      # a new run: the session starts over too
        self.refresh()
        if first_time and not self.settings.help_seen:
            self.settings.help_seen = True
            self.settings.save()
            self.show_help()

    # ---- building the UI
    def build_side(self):
        f = QFrame()
        f.setObjectName('panel')
        f.setFixedWidth(280)
        self.side = f
        lay = QVBoxLayout(f)
        lay.setSpacing(4)
        self.lbl_day = QLabel()
        self.lbl_day.setObjectName('bigDay')
        lay.addWidget(self.lbl_day)
        self.lbl_job = QLabel()
        self.lbl_job.setObjectName('hint')
        self.lbl_job.setWordWrap(True)
        lay.addWidget(self.lbl_job)
        lay.addSpacing(4)
        lay.addWidget(section(tr('WALLET')))
        self.lbl_balance = QLabel()
        self.lbl_balance.setObjectName('bigMoney')
        lay.addWidget(self.lbl_balance)
        self.lbl_bank = QLabel()
        self.lbl_bank.setObjectName('bank')
        lay.addWidget(self.lbl_bank)
        self.lbl_debt = QLabel()
        self.lbl_debt.setObjectName('debt')
        self.lbl_debt.setWordWrap(True)             # bank debt + shark debt must both stay readable
        lay.addWidget(self.lbl_debt)
        lay.addSpacing(4)
        self.lbl_level = section('')
        lay.addWidget(self.lbl_level)
        self.bar_exp = QProgressBar()
        self.bar_exp.setStyleSheet('QProgressBar::chunk{background:#6c8cff;border-radius:7px;}')
        lay.addWidget(self.bar_exp)
        self.lbl_mental = section('')
        lay.addWidget(self.lbl_mental)
        self.bar_mental = QProgressBar()
        self.bar_mental.setRange(0, 100)
        lay.addWidget(self.bar_mental)
        self.lbl_streak = section('')
        lay.addWidget(self.lbl_streak)
        self.bar_streak = QProgressBar()
        self.bar_streak.setRange(0, 7)
        self.bar_streak.setFormat('%v / 7')
        lay.addWidget(self.bar_streak)
        lay.addWidget(section(tr('GOAL')))
        self.bar_goal = QProgressBar()
        self.bar_goal.setStyleSheet('QProgressBar::chunk{background:#d4a017;border-radius:7px;}')
        lay.addWidget(self.bar_goal)
        lay.addSpacing(4)
        self.lbl_nogamble, self.lbl_today = QLabel(), QLabel()
        self.lbl_skipped, self.lbl_limits = QLabel(), QLabel()
        self.lbl_items = QLabel()
        self.lbl_items.setObjectName('hint')
        for w in (self.lbl_nogamble, self.lbl_today, self.lbl_skipped, self.lbl_limits, self.lbl_items):
            w.setWordWrap(True)
            lay.addWidget(w)
        self.lbl_status = QLabel()
        self.lbl_status.setObjectName('status')
        self.lbl_status.setWordWrap(True)
        lay.addWidget(self.lbl_status)
        lay.addStretch()
        return f

    def build_lobby(self):
        inner = QWidget()
        lay = QVBoxLayout(inner)
        lay.setContentsMargins(0, 0, 8, 0)
        lay.setSpacing(8)
        bar = QFrame()
        bar.setObjectName('panel')
        bl = QHBoxLayout(bar)
        bl.addWidget(QLabel(tr('Your bet (TL):')))
        self.bet_spin = QSpinBox()
        self.bet_spin.setRange(1, 100)
        self.bet_spin.setValue(10)
        self.bet_spin.setMinimumWidth(140)
        self.bet_spin.setFocusPolicy(Qt.FocusPolicy.ClickFocus)       # so the number keys can start games
        self.bet_spin.editingFinished.connect(self.setFocus)
        bl.addWidget(self.bet_spin)
        for text, fn in ((tr('Min'), lambda: self.bet_spin.setValue(1)),
                         ('½', lambda: self.bet_spin.setValue(max(1, self.bet_spin.value() // 2))),
                         ('×2', lambda: self.bet_spin.setValue(self.bet_spin.value() * 2)),
                         (tr('Max'), lambda: self.bet_spin.setValue(self.bet_spin.maximum()))):
            b = Button(text)
            b.clicked.connect(fn)
            bl.addWidget(b)
        self.lbl_maxbet = QLabel()
        self.lbl_maxbet.setObjectName('hint')
        bl.addWidget(self.lbl_maxbet)
        bl.addStretch()
        lay.addWidget(bar)

        # ---- streak side bet (B6): stake a fixed amount on winning N one-shot games in a row
        lay.addWidget(section(tr('STREAK BET')))
        sb_panel = QFrame()
        sb_panel.setObjectName('panel')
        sbl = QVBoxLayout(sb_panel)
        sbl.setContentsMargins(12, 8, 12, 8)
        sbl.setSpacing(6)
        sb_top = QHBoxLayout()
        sb_top.addWidget(QLabel(tr('Stake (TL):')))
        self.sb_spin = QSpinBox()
        self.sb_spin.setRange(1, 100)
        self.sb_spin.setValue(10)
        self.sb_spin.setMinimumWidth(120)
        self.sb_spin.setFocusPolicy(Qt.FocusPolicy.ClickFocus)       # digits stay for starting games
        self.sb_spin.valueChanged.connect(self.streak_labels)
        sb_top.addWidget(self.sb_spin)
        sb_top.addStretch()
        sbl.addLayout(sb_top)
        sb_row = QHBoxLayout()
        self.sb_btns = {}
        for target in (3, 5, 7, 10):
            b = Button()
            b.setObjectName('gameBtn')
            b.clicked.connect(lambda _=False, t=target: self.place_streak(t))
            sb_row.addWidget(b)
            self.sb_btns[target] = b
        sbl.addLayout(sb_row)
        self.sb_cash = Button(tr('CASH OUT THE STREAK BET'))
        self.sb_cash.clicked.connect(self.cash_streak)
        self.sb_cash.setVisible(False)
        sbl.addWidget(self.sb_cash)
        self.sb_prog = QLabel()
        self.sb_prog.setObjectName('hint')
        self.sb_prog.setWordWrap(True)
        sbl.addWidget(self.sb_prog)
        lay.addWidget(sb_panel)

        self.lobby_keys = {}
        self.game_btns = {}
        for cat, keys in CATEGORIES:
            lay.addWidget(section(tr(cat)))
            row = QHBoxLayout()
            for k in keys:
                b = Button()
                b.setObjectName('gameBtn')
                b.setStyleSheet(f'QPushButton#gameBtn {{ border-left:4px solid {CATEGORY_ACCENTS[cat]}; }}')
                b.clicked.connect(lambda _=False, k=k: self.start_game(k))
                row.addWidget(b)
                self.game_btns[k] = b
                i = LOBBY_ORDER.index(k)
                self.lobby_keys[(DIGITS[i % 10], i >= 10)] = b          # 1-9, 0, then Alt+1..6
            lay.addLayout(row)

        def grid(items):
            g = QGridLayout()
            for c in range(3):
                g.setColumnStretch(c, 1)
            for i, (label, key, fn, name, action) in enumerate(items):
                b = Button(label)
                if name:
                    b.setObjectName(name)
                b.clicked.connect(fn)
                g.addWidget(b, i // 3, i % 3)
                if action:
                    self.action_btns[action] = b
                    if key != K.Key_unknown:
                        self.lobby_keys[(key, False)] = b
            return g

        # D6: which key runs which action can be changed in Settings -> Key bindings
        self.keyname = self.settings.keymap()
        self.action_btns, self.action_text = {}, {}

        def act(action, title, suffix='', fn=None, name=None):
            self.action_text[action] = (title, suffix)
            return (f'{title}  [{self.keyname[action]}]' + (f'\n{suffix}' if suffix else ''),
                    key_from_name(self.keyname[action]), fn, name, action)

        lay.addWidget(section(tr('LIFE & MONEY')))
        life = grid([act('work', tr('Go to Work'), fn=self.go_work),
                     act('day', tr('Pass Day'), fn=self.pass_day),
                     act('out', tr('Go out with loved one'), '100 TL  •  7 days', fn=self.go_out),
                     act('bank', tr('Bank && Loans'), fn=self.show_bank),
                     act('jobs', tr('Jobs'), fn=self.show_jobs),
                     act('shop', tr('Shop'), fn=self.show_shop)])
        self.work_btn = self.action_btns['work']
        self.out_btn = self.action_btns['out']
        lay.addLayout(life)
        lay.addWidget(section(tr('TOURNAMENT')))
        self.tour_btn = Button(tr('Enter tournament'))
        self.tour_btn.setObjectName('primary')
        self.tour_btn.clicked.connect(self.toggle_tournament)
        lay.addWidget(self.tour_btn)
        self.tour_lbl = QLabel()
        self.tour_lbl.setWordWrap(True)
        self.tour_lbl.setObjectName('itemDesc')
        lay.addWidget(self.tour_lbl)
        self.sprint_btn = Button(txf('Sprint  •  {e} TL, {d} days', e='0', d=3))   # D12 (text set in refresh)
        self.sprint_btn.clicked.connect(self.toggle_sprint)
        lay.addWidget(self.sprint_btn)
        self.sprint_lbl = QLabel()
        self.sprint_lbl.setWordWrap(True)
        self.sprint_lbl.setObjectName('itemDesc')
        lay.addWidget(self.sprint_lbl)
        lay.addWidget(section(tr('MENU')))
        lay.addLayout(grid([act('stats', tr('Statistics'), fn=self.show_stats),
                            act('ach', tr('Achievements'), fn=self.show_achievements),
                            (tr('Trophy room'), K.Key_unknown, self.show_trophies, None, None),   # D11
                            act('help', tr('How to Play'), fn=self.show_help),
                            act('settings', tr('Settings'), fn=self.open_settings),
                            (tr('Reset Game'), K.Key_unknown, self.reset_game, 'danger', None),
                            (tr('Save && Quit'), K.Key_unknown, self.close, None, None)]))
        lay.addStretch()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidget(inner)
        scroll.viewport().setAutoFillBackground(False)
        return scroll

    # ---- keyboard
    @staticmethod
    def trigger(target):
        if isinstance(target, QAbstractButton):
            if target.isVisible() and target.isEnabled():
                target.click()
                return True
            return False
        target()
        return True

    def keyPressEvent(self, e):
        key = e.key()
        alt = bool(e.modifiers() & Qt.KeyboardModifier.AltModifier)
        if key == K.Key_Escape:
            self.go_back()
            e.accept()
            return
        cur = self.stack.currentWidget()
        if cur is self.lobby:
            targets = [self.lobby_keys[(key, alt)]] if (key, alt) in self.lobby_keys else []
        elif cur is self.game_page and not alt:
            targets = self.game_page.keys.get(key, [])
        else:
            targets = []
        for t in targets:
            if self.trigger(t):
                e.accept()
                return
        super().keyPressEvent(e)

    def go_back(self):
        if self.focusWidget() in (self.bet_spin, self.sb_spin):   # Esc first leaves the amount box
            self.setFocus()
            return
        cur = self.stack.currentWidget()
        if cur is self.lobby:
            self.exit_fullscreen()
        elif cur is self.game_page and self.game_page.in_progress:
            return                                          # no walking out of a round
        else:
            self.show_lobby()

    # ---- display settings and small visual effects
    def anim_factor(self):
        return ANIM_SPEEDS[self.settings.anim][1]

    def apply_settings(self, initial=False):
        st = self.settings
        if current() != st.lang:                       # D9: the language was switched in Settings
            return self.retranslate(st.lang)
        QApplication.instance().setStyleSheet(build_style(st.theme, st.text))
        self.logbox.setVisible(st.show_log)
        self.side.setFixedWidth(round(280 + (TEXT_SCALES[st.text][1] - 1) * 200))
        sound.set_enabled(st.sound)                          # D5: sound effects on/off
        set_card_scale(CARD_SIZES[st.cards][1][0] / 68)      # D7: how big the cards are drawn
        if not initial and getattr(self, 'keyname', None) and st.keymap() != self.keyname:
            self.rebind_keys()                               # D6: the hotkeys were changed
        if not initial:
            if st.fullscreen and not self.isFullScreen():
                self.showFullScreen()
            elif not st.fullscreen and self.isFullScreen():
                self.showNormal()
        self.fs_btn.setText(tr('⛶  Exit fullscreen') if st.fullscreen else tr('⛶  Fullscreen'))
        st.save()

    def retranslate(self, lang):
        """D9: rebuild every widget in the new language. The run, the engine and the session are
        untouched - only the texts change. Returns without doing anything while a hand is on
        the table (Settings cannot be opened then, but be safe)."""
        if self.round_running():
            self.settings.lang = current()
            return
        set_lang(lang)
        old = self.centralWidget()
        # the stack holds the wrapped pages (a scroll area), so compare against the wrapper
        current = self.stack.currentWidget() if hasattr(self, 'stack') else None
        key = next((k for k in ('bank', 'stats', 'jobs', 'ach', 'shop', 'help', 'trophy')
                    if current is self.page_wrap.get(getattr(self, f'{k}_page', None))), None)
        self.build_ui()                                # rebuilds in the new language, then re-applies
        if old is not None:
            old.deleteLater()
        self._last_balance = None
        target = getattr(self, f'{key}_page') if key else self.lobby
        self.stack.setCurrentWidget(self.page_wrap.get(target, target))
        if key:                                          # the rebuilt page starts empty
            target.refresh()
        self.refresh()
        self.settings.save()

    def rebind_keys(self):
        """D6: point the lobby buttons at their new keys and repaint their labels."""
        self.keyname = self.settings.keymap()
        for (k, alt), b in list(self.lobby_keys.items()):
            if any(b is ab for ab in self.action_btns.values()):
                del self.lobby_keys[(k, alt)]
        for action, b in self.action_btns.items():
            self.lobby_keys[(key_from_name(self.keyname[action]), False)] = b
            title, suffix = self.action_text[action]
            b.setText(f'{title}  [{self.keyname[action]}]' + (f'\n{suffix}' if suffix else ''))
        self.refresh()

    def toggle_fullscreen(self):
        self.settings.fullscreen = not self.isFullScreen()
        self.apply_settings()

    def exit_fullscreen(self):
        if self.isFullScreen():
            self.settings.fullscreen = False
            self.apply_settings()

    def open_settings(self):
        if self.round_running():
            return self.log('Finish the hand first - the bet is still on the table.', 'warn')
        SettingsDialog(self).exec()
        self.apply_settings()                          # the language is applied once the dialog is gone

    def show_window(self):
        if self.settings.fullscreen:
            self.showFullScreen()
        else:
            self.show()

    def celebrate(self):
        if self.settings.effects and hasattr(self, 'confetti'):
            self.confetti.burst()
        sound.play('jackpot')

    def set_balance(self, value):
        """D2: the wallet number rolls to its new value instead of jumping."""
        target = int(value)
        if self._ticker is not None:
            self._ticker.stop()
            self._ticker.deleteLater()                # one animation per wallet roll, not one per session
            self._ticker = None
        if not (self.settings.effects and self.anim_factor() > 0 and self._last_balance is not None
                and target != self._last_balance and alive(self.lbl_balance)):
            self.lbl_balance.setText(f'{target:,} TL')
            return
        anim = QVariantAnimation(self)
        anim.setStartValue(int(self._last_balance))
        anim.setEndValue(target)
        anim.setDuration(max(160, round(450 * self.anim_factor())))
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim.valueChanged.connect(lambda v: self.lbl_balance.setText(f'{int(v):,} TL'))
        anim.finished.connect(lambda: self.lbl_balance.setText(f'{target:,} TL')
                              if alive(self.lbl_balance) else None)
        self._ticker = anim
        anim.start()

    def balloon(self, text, color):
        """D3: a little speech balloon that pops up over the table and drifts away."""
        if not self.settings.effects or self.anim_factor() <= 0:
            return
        host = self.centralWidget()
        if host is None or not alive(host):
            return
        lbl = QLabel(text, host)
        lbl.setStyleSheet(f'background:rgba(0,0,0,0.78);color:{color};border:2px solid {color};'
                          'border-radius:14px;padding:8px 18px;font-size:18px;font-weight:800;')
        lbl.adjustSize()
        x = max(8, (host.width() - lbl.width()) // 2)
        y = round(host.height() * 0.20)
        start = QPoint(x, y)
        lbl.move(start)
        lbl.show()
        lbl.raise_()
        end = QRect(start.x(), start.y(), lbl.width(), lbl.height())
        pop = QRect(start.x() + lbl.width() // 4, start.y() + lbl.height() // 2,
                    max(8, lbl.width() // 2), max(4, lbl.height() // 2))
        grow = QPropertyAnimation(lbl, b'geometry', lbl)
        grow.setStartValue(pop)
        grow.setEndValue(end)
        grow.setDuration(220)
        grow.setEasingCurve(QEasingCurve.Type.OutBack)
        effect = QGraphicsOpacityEffect(lbl)
        lbl.setGraphicsEffect(effect)
        rise = QPropertyAnimation(lbl, b'pos', lbl)
        rise.setStartValue(start)
        rise.setEndValue(start + QPoint(0, -44))
        rise.setDuration(1100)
        rise.setEasingCurve(QEasingCurve.Type.OutCubic)
        fade = QPropertyAnimation(effect, b'opacity', lbl)
        fade.setStartValue(1.0)
        fade.setEndValue(0.0)
        fade.setDuration(1100)
        fade.setEasingCurve(QEasingCurve.Type.InQuad)
        tail = QParallelAnimationGroup(lbl)
        for a in (rise, fade):
            tail.addAnimation(a)
        seq = QSequentialAnimationGroup(lbl)
        seq.addAnimation(grow)
        seq.addPause(240)                              # let the balloon pop before it drifts
        seq.addAnimation(tail)
        seq.finished.connect(lbl.deleteLater)
        seq.start()

    def session_text(self):
        """D1: what this sitting actually did, in one short paragraph."""
        s = self.state
        ses = self.session
        minutes = max(0, round((time.time() - ses['start']) / 60))
        net = s.net_worth - ses['net0']
        return (txf('{m} min  •  day {d}  •  {g} games', m=minutes, d=s.day, g=ses["games"])
                + ' ' + txf('({w} won, {l} lost)', w=ses["wins"], l=ses["games"] - ses["wins"]) + '\n'
                + txf('Best round: +{n} TL', n=f'{ses["best"]:,}') + '     '
                + txf('Net worth this session: {n} TL', n=f'{net:+,}') + '\n'
                + txf('Now: {n} TL', n=f'{s.net_worth:,}'))

    def share_result(self):
        """D10: render the result card, save it next to the save files and copy it."""
        try:
            path = share.share(self)
        except Exception as exc:                          # never let sharing break the game
            return self.log(txf('Could not share the result card: {e}', e=exc), 'loss')
        self.log(txf('Result card saved to {p} - also copied to the clipboard.', p=path), 'win')
        return path

    def flash_delta(self, delta):
        """A floating +/- amount next to the wallet."""
        if not self.settings.effects:
            return
        host = self.centralWidget()
        lbl = QLabel(f'{delta:+,} TL', host)
        size = round(20 * TEXT_SCALES[self.settings.text][1])
        lbl.setStyleSheet(f'color:{"#4cc38a" if delta > 0 else "#ff6b6b"};font-size:{size}px;'
                          'font-weight:800;background:transparent;')
        lbl.adjustSize()
        origin = self.lbl_balance.mapTo(host, QPoint(0, 0))
        start = QPoint(origin.x() + self.lbl_balance.width() - lbl.width() - 4, origin.y() + 2)
        lbl.move(start)
        lbl.show()
        lbl.raise_()
        effect = QGraphicsOpacityEffect(lbl)
        lbl.setGraphicsEffect(effect)
        move = QPropertyAnimation(lbl, b'pos', lbl)
        move.setStartValue(start)
        move.setEndValue(start + QPoint(0, -30))
        move.setEasingCurve(QEasingCurve.Type.OutCubic)
        fade = QPropertyAnimation(effect, b'opacity', lbl)
        fade.setStartValue(1.0)
        fade.setEndValue(0.0)
        fade.setEasingCurve(QEasingCurve.Type.InQuad)
        group = QParallelAnimationGroup(lbl)
        for a in (move, fade):
            a.setDuration(1300)
            group.addAnimation(a)
        group.finished.connect(lbl.deleteLater)
        group.start()

    # ---- log and refresh
    def log(self, msg, kind='info'):
        color = {'info': '#d6d9e3', 'win': '#4cc38a', 'loss': '#ff6b6b', 'warn': '#f4c542'}.get(kind, '#d6d9e3')
        self.logbox.append(f'<span style="color:{color}">{html.escape(msg)}</span>')

    def refresh(self):
        eng, s = self.engine, self.state
        eng.check_achievements()
        if self._last_balance is not None and s.balance != self._last_balance:
            self.flash_delta(s.balance - self._last_balance)
        self._last_balance = s.balance
        lv = s.level
        self.lbl_day.setText(txf('Day {n}', n=s.day))
        self.lbl_job.setText(f'{s.diff["name"]} {tr("difficulty")}  •  {s.job_info["name"]}  •  '
                             f'{self.engine.tenure_title()} ({txf("{n} days worked", n=s.worked_days)})')
        self.set_balance(s.balance)                        # D2: rolls to the new number
        self.lbl_bank.setText(txf('Bank: {n} TL', n=f'{s.bank:,.2f}'))
        parts = []
        if s.debt > 0:
            parts.append(txf('Debt: {n} TL', n=f'{s.debt:,}'))
        if s.shark_debt > 0:                    # the loan shark's share, in red next to the bank debt
            parts.append(txf('Shark: {n} TL (collects day {d})', n=f'{s.shark_debt:,}', d=s.shark_due))
        self.lbl_debt.setText('   •   '.join(parts))
        self.lbl_debt.setVisible(bool(parts))
        self.lbl_level.setText(txf('LEVEL {n}', n=lv))
        cur, need, is_max = eng.level_progress()
        self.bar_exp.setRange(0, need)
        self.bar_exp.setValue(need if is_max else cur)
        self.bar_exp.setFormat(txf('{n} exp (MAX)', n=s.exp) if is_max
                               else txf('{a} / {b} exp', a=s.exp, b=LEVEL_EXP[lv]))
        face = '😄' if s.mental > 80 else '🙂' if s.mental > 60 else '😐' if s.mental > 40 else '😟' if s.mental > 20 else '😵'
        self.lbl_mental.setText(f'{tr("MENTAL HEALTH")}  {face}  {s.mental}/100')
        self.bar_mental.setValue(s.mental)
        color = '#4cc38a' if s.mental > 60 else '#e0a526' if s.mental > 30 else '#e5484d'
        self.bar_mental.setStyleSheet(f'QProgressBar::chunk{{background:{color};border-radius:7px;}}')
        self.lbl_streak.setText(f'{tr("WORK STREAK")}   {s.work_streak}/7')
        self.bar_streak.setValue(min(7, s.work_streak))
        nw = s.net_worth
        self.bar_goal.setRange(0, s.goal)
        self.bar_goal.setValue(max(0, min(s.goal, nw)))
        self.bar_goal.setFormat(txf('{n} / {g} TL', n=f'{nw:,}', g=f'{s.goal:,}'))
        self.lbl_nogamble.setText(txf('No Gamble Days: {a}/{b}', a=s.no_gamble_days, b=CLEAN_TARGET))
        self.lbl_today.setText(tr('Games today: ') + '●' * s.games_today + '○' * max(0, 5 - s.games_today)
                               + f'  {s.games_today}/5')
        self.lbl_skipped.setText(txf('Skipped days (no games): {n}', n=s.skipped_days))
        streaks = (f'{s.clean_streaks}/{CLEAN_STREAKS_FOR_ENDING}' if s.clean_streaks < CLEAN_STREAKS_FOR_ENDING
                   else f'{s.clean_streaks} ✓')
        self.lbl_limits.setText(txf('Clean streaks: {s}   •   Credit limit: {c} TL',
                                    s=streaks, c=f'{s.credit_limit:,}'))
        owned = [f'{ITEM_BY_KEY[k]["name"]}' + (f' ×{n}' if ITEM_BY_KEY[k]['kind'] == 'consumable' else '')
                 for k, n in s.items.items() if n > 0 and k in ITEM_BY_KEY]
        self.lbl_items.setText(tr('Items: ') + ', '.join(owned) if owned else '')
        self.lbl_items.setVisible(bool(owned))
        status = []
        if s.out_days > 0:
            status.append(txf('Protected from mental health loss for {n} more day(s).', n=s.out_days))
        if s.work_cooldown > 0:
            status.append(txf('Too tired to work for {n} more day(s).', n=s.work_cooldown))
        self.lbl_status.setText('\n'.join(status))

        if s.tour_active:                       # TOURNAMENT panel: running window vs. the entry button
            running = getattr(s, 'tour_mode', 'classic') == 'classic'
            day_no = min(s.day - s.tour_day + 1, TOURNAMENT_DAYS)   # day 1 on the day you entered
            self.tour_btn.setText(txf('Tournament running  •  day {a}/{b}', a=day_no, b=TOURNAMENT_DAYS)
                                  if running else txf('Enter tournament  •  {e} TL, {d} days',
                                                      e=f'{TOURNAMENT_ENTRY:,}', d=TOURNAMENT_DAYS))
            self.tour_btn.setEnabled(False if running else not s.tour_active and s.balance >= TOURNAMENT_ENTRY)
            self.tour_lbl.setText(
                txf('Started day {d} at {n} TL. Now {m} TL ({g} TL). Finish in the black on day {end} to '
                    'get the {e} TL entry back, plus {p}% of your growth.',
                    d=s.tour_day, n=f'{s.tour_net:,}', m=f'{s.net_worth:,}',
                    g=f'{s.net_worth - s.tour_net:+,}', end=s.tour_day + TOURNAMENT_DAYS,
                    e=f'{TOURNAMENT_ENTRY:,}', p=f'{TOURNAMENT_BONUS_RATE * 100:.0f}')
                if running else self._classic_tour_text())
        else:
            self.tour_btn.setText(txf('Enter tournament  •  {e} TL, {d} days',
                                      e=f'{TOURNAMENT_ENTRY:,}', d=TOURNAMENT_DAYS))
            self.tour_btn.setEnabled(not s.tour_active and s.balance >= TOURNAMENT_ENTRY)
            self.tour_lbl.setText(self._classic_tour_text())
        self.tour_lbl.setVisible(True)

        sprinting = s.tour_active and getattr(s, 'tour_mode', 'classic') == 'sprint'   # D12
        if sprinting:
            day_no = min(s.day - s.tour_day + 1, TOURNAMENT_SPRINT_DAYS)
            self.sprint_btn.setText(txf('Sprint running  •  day {a}/{b}', a=day_no,
                                        b=TOURNAMENT_SPRINT_DAYS))
            self.sprint_btn.setEnabled(False)
            self.sprint_lbl.setText(
                txf('Sprint: started day {d} at {n} TL. Now {m} TL ({g} TL). Finish in the black on day '
                    '{end} to get the {e} TL entry back, plus {p}% of your growth.',
                    d=s.tour_day, n=f'{s.tour_net:,}', m=f'{s.net_worth:,}',
                    g=f'{s.net_worth - s.tour_net:+,}', end=s.tour_day + TOURNAMENT_SPRINT_DAYS,
                    e=f'{TOURNAMENT_SPRINT_ENTRY:,}', p=f'{TOURNAMENT_SPRINT_BONUS_RATE * 100:.0f}'))
        else:
            sbest = getattr(self.meta, 'sprints', {}).get(s.difficulty, 0)
            self.sprint_btn.setText(txf('Sprint  •  {e} TL, {d} days',
                                        e=f'{TOURNAMENT_SPRINT_ENTRY:,}', d=TOURNAMENT_SPRINT_DAYS))
            self.sprint_btn.setEnabled(not s.tour_active and s.balance >= TOURNAMENT_SPRINT_ENTRY)
            self.sprint_lbl.setText(
                txf('A 3-day dash against your own net worth: {p}% of the growth back on top, capped at '
                    '{c} TL. Only one tournament at a time. Best sprint on {diff}: {best}.',
                    p=f'{TOURNAMENT_SPRINT_BONUS_RATE * 100:.0f}', c=f'{TOURNAMENT_SPRINT_BONUS_CAP:,}',
                    diff=s.diff["name"], best=f'{sbest:+,} TL' if sbest else '-'))
        self.sprint_lbl.setVisible(True)

        self.bet_spin.setRange(1, max(1, min(s.balance, s.max_bet, 2_000_000_000)))
        self.lbl_maxbet.setText(tr('max bet: ') + (tr('no limit') if s.max_bet >= 10 ** 9
                                                   else txf('{n} TL', n=f'{s.max_bet:,}')))
        for k, b in self.game_btns.items():
            if lv >= UNLOCK[k]:
                b.setText(f'{GAME_ICONS[k]}  {tr(GAME_NAMES[k])}   [{GAME_HOTKEYS[k]}]\n{tr(GAME_SUBTITLES[k])}')
                b.setEnabled(s.balance >= 1)
            else:
                b.setText(f'{GAME_ICONS[k]}  {tr(GAME_NAMES[k])}\n🔒 {txf("Unlocks at level {n}", n=UNLOCK[k])}')
                b.setEnabled(False)
        wk = self.keyname.get('work', 'W')
        if s.work_cooldown == 0:
            self.work_btn.setText(f'{tr("Go to Work")}  [{wk}]\n{s.job_info["name"]}: +{eng.work_pay()} TL')
        else:
            self.work_btn.setText(f'{tr("Go to Work")}  [{wk}]\n'
                                  + txf('Too tired ({n} day(s))', n=s.work_cooldown))
        self.work_btn.setEnabled(s.work_cooldown == 0)
        self.out_btn.setEnabled(s.balance >= 100)
        self.streak_labels()
        self.bank_page.refresh()

    # ---- endings and events
    def handle_endings(self):
        """Shows the ending dialog if the run is over. Returns True if a new run was started."""
        key = self.engine.check_endings()
        if not key:
            return False
        dlg = EndingDialog(self, key, self.state, self.meta)
        dlg.exec()
        if dlg.start_over:
            self.ask_new_game()
        else:
            self.engine.save()
        self.refresh()
        return dlg.start_over

    def process_events(self):
        eng = self.engine
        while eng.pending_events and self.game_page is None and self.stack.currentWidget() is self.lobby:
            ev = eng.pending_events.pop(0)
            dlg = EventDialog(self, ev, self.state)
            dlg.exec()
            eng.run_event(ev, dlg.choice if dlg.choice is not None else len(ev['choices']) - 1)
            self.refresh()
            if self.handle_endings():
                break

    def after_life_action(self):
        self.refresh()
        if not self.handle_endings():
            self.process_events()

    # ---- navigation
    def round_running(self):
        """True while a bet is still on the table: nothing may navigate away, or the round would
        be destroyed before it settles and the player could replay the same bet for free."""
        return self.game_page is not None and bool(getattr(self.game_page, 'in_progress', False))

    def leave_game_page(self):
        if self.game_page is not None:
            if self.round_running():
                return False                     # settle the hand first
            self.stack.removeWidget(self.game_page)
            self.game_page.deleteLater()
            self.game_page = None
        return True

    def set_page(self, w):
        if not self.leave_game_page():
            return False
        self.game_page = w
        self.stack.addWidget(w)
        self.stack.setCurrentWidget(w)
        return True

    def show_lobby(self):
        if not self.leave_game_page():
            return self.log('Finish the hand first - the bet is still on the table.', 'warn')
        self.stack.setCurrentWidget(self.lobby)
        self.refresh()
        if not self.handle_endings():
            self.process_events()

    @staticmethod
    def scrollable(page):
        """Long pages (statistics, achievements...) scroll instead of clipping their last rows."""
        sc = QScrollArea()
        sc.setWidgetResizable(True)
        sc.setFrameShape(QFrame.Shape.NoFrame)
        sc.setWidget(page)
        sc.viewport().setAutoFillBackground(False)
        return sc

    def show_page(self, page):
        if self.round_running():                 # F1 / B / T ... during a round must not void it
            return self.log(tr('Finish the hand first - the bet is still on the table.'), 'warn')
        page.refresh()
        self.stack.setCurrentWidget(self.page_wrap.get(page, page))

    def show_bank(self):
        self.show_page(self.bank_page)

    def show_stats(self):
        self.show_page(self.stats_page)

    def show_jobs(self):
        self.show_page(self.jobs_page)

    def show_achievements(self):
        self.show_page(self.ach_page)

    def show_shop(self):
        self.show_page(self.shop_page)

    def show_trophies(self):                            # D11
        self.show_page(self.trophy_page)

    def show_help(self):
        self.show_page(self.help_page)

    def start_game(self, key):
        s, bet = self.state, self.bet_spin.value()
        if self.round_running():
            return self.log(tr('Finish the hand first - the bet is still on the table.'), 'warn')
        if s.level < UNLOCK[key]:
            return self.log(txf('{n} unlocks at level {l}.', n=tr(GAME_NAMES[key]), l=UNLOCK[key]), 'warn')
        if s.balance < 1 or bet <= 0 or bet > s.balance:
            return self.log(tr('Invalid bet amount!'), 'warn')
        if bet > s.max_bet:
            return self.log(txf('The maximum bet at your level is {n:,} TL.', n=s.max_bet), 'warn')
        self.set_page(GAMES[key](self, bet))

    def play_again(self, key, bet):
        if self.handle_endings():
            return self.show_lobby()
        self.bet_spin.setValue(min(bet, max(1, self.state.balance), self.state.max_bet))
        self.start_game(key)

    def finish_round(self, key, delta, win, bet, tags, insured):
        self.engine.finish_game(key, delta, win, bet, tags, insured)
        ses = self.session                              # D1: what this sitting has been doing
        ses['games'] += 1
        ses['wins'] += win is True
        ses['best'] = max(ses['best'], delta)
        self.refresh()
        sound.play('jackpot' if 'jackpot' in tags else 'win' if delta > 0 else
                   'lose' if delta < 0 else None)       # D5
        if delta != 0:                                  # D3: a floating chip of the result
            self.balloon(f'{tr(GAME_NAMES[key])}   {delta:+,} TL',
                         '#f4c542' if 'jackpot' in tags else '#4cc38a' if delta > 0 else '#ff6b6b')

    # ---- streak side bet (B6)
    def place_streak(self, target):
        if not self.engine.place_streak(target, self.sb_spin.value()):
            return self.log(tr('Streak bet not placed: one is already running, or you cannot afford the '
                               'stake.'), 'warn')
        self.refresh()

    def streak_labels(self):
        """Repaint the four streak-bet buttons (their payout depends on the stake in the box)."""
        stake, s = self.sb_spin.value(), self.state
        for target, b in self.sb_btns.items():
            mult = config.STREAK_BETS[target]
            odds = config.STREAK_P_MAX ** target
            b.setText(txf('{n} in a row', n=target) + f'\n{mult:g}×  →  {int(stake * mult):,} TL'
                      + (f'\n{odds * 100:.1f}% ' + tr('chance') if s.has('streak_book') else ''))
            b.setEnabled(not s.sb_stake and stake <= s.balance)
        self.sb_spin.setEnabled(not s.sb_stake)
        if s.sb_stake:
            self.sb_prog.setText(
                txf('RUNNING: {a}/{b} won  •  {s} TL at stake  •  pays {m:g}× = {v} TL  •  '
                    'a loss in a one-shot game drops it.',
                    a=s.sb_count, b=s.sb_target, s=f'{s.sb_stake:,}',
                    m=config.STREAK_BETS[s.sb_target],
                    v=f'{int(s.sb_stake * config.STREAK_BETS[s.sb_target]):,}'))
            self.sb_prog.setStyleSheet('color:#f4c542;')
            can_cash = s.has('streak_book') and s.sb_count > 0
            self.sb_cash.setVisible(can_cash)
            if can_cash:
                value = self.engine.streak_cash_value()
                self.sb_cash.setText(txf('CASH OUT NOW FOR {v} TL  (fair value, no gamble)',
                                         v=f'{value:,}'))
                self.sb_cash.setEnabled(value > 0)
        else:
            self.sb_prog.setText(
                tr('Win 3, 5, 7 or 10 one-shot games in a row to take the payout. The stake is paid up '
                   'front and cannot be refunded. Crash, Mines and Hi-Lo neither count nor break it; a '
                   'push is neutral.'))
            self.sb_prog.setStyleSheet('')
            self.sb_cash.setVisible(False)

    def cash_streak(self):
        if self.engine.cash_out_streak():
            self.refresh()

    # ---- tournament (the engine holds the entry fee and scores the window)
    def _classic_tour_text(self):
        """The standing description of the 10-day tournament (also shown while a sprint runs)."""
        best = getattr(self.meta, 'tournaments', {}).get(self.state.difficulty, 0)
        return txf('A race against your own net worth. The entry is held; finish ahead and you get it back '
                   'plus {p}% of the growth (capped), finish behind and it is gone. Best on {diff}: {best}.',
                   p=f'{TOURNAMENT_BONUS_RATE * 100:.0f}', diff=self.state.diff["name"],
                   best=f'{best:+,} TL' if best else '-')

    def toggle_tournament(self):
        self.engine.enter_tournament('classic')
        self.refresh()

    def toggle_sprint(self):                              # D12: the 3-day side race
        self.engine.enter_tournament('sprint')
        self.refresh()

    # ---- life actions (the engine does the work)
    def go_work(self):
        self.engine.go_work()
        self.after_life_action()

    def pass_day(self):
        self.engine.pass_day()
        self.after_life_action()

    def go_out(self):
        self.engine.go_out()
        self.refresh()

    def reset_game(self):
        r = QMessageBox.question(self, tr('Reset game'),
                                 tr('Delete your current run and start over?\n(Achievements and endings '
                                    'are kept.)'))
        if r == QMessageBox.StandardButton.Yes:
            self.leave_game_page()
            self.stack.setCurrentWidget(self.lobby)
            self.ask_new_game()

    def closeEvent(self, e):
        if self.game_page is not None and self.game_page.in_progress:
            QMessageBox.information(self, tr('Game in progress'),
                                    tr('Finish the current round before quitting.'))
            e.ignore()
            return
        self.engine.save()
        if self.session['games'] > 0 and not getattr(self, '_summary_shown', False):   # D1
            self._summary_shown = True
            box = QMessageBox(self)
            box.setWindowTitle(tr('Session summary'))
            box.setIcon(QMessageBox.Icon.NoIcon)
            box.setText(f'{tr("This session")}\n\n{self.session_text()}')
            share_btn = box.addButton(tr('📸  Share result card'), QMessageBox.ButtonRole.ActionRole)
            box.addButton(QMessageBox.StandardButton.Ok)
            box.exec()
            if box.clickedButton() is share_btn:          # D10: leave with a card in hand
                self.share_result()
        e.accept()
