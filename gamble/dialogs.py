"""Modal dialogs: random events, endings, settings, key bindings and the new-game difficulty picker."""
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QCheckBox, QComboBox, QDialog, QFrame, QGridLayout, QHBoxLayout, QLabel, QVBoxLayout

from .config import ACHIEVEMENTS, DIFFICULTIES, ENDINGS
from .i18n import LANGUAGES, current, tr, txf
from .style import ANIM_SPEEDS, CARD_SIZES, DEFAULT_KEYS, KEY_NAMES, TEXT_SCALES, THEMES
from .widgets import Button, page_title, section

K = Qt.Key

_SPECIAL = {'ESC': K.Key_Escape, 'ESCAPE': K.Key_Escape, 'SPACE': K.Key_Space, 'ENTER': K.Key_Return,
            'RETURN': K.Key_Return, 'TAB': K.Key_Tab, 'BACKSPACE': K.Key_Backspace, 'UP': K.Key_Up,
            'DOWN': K.Key_Down, 'LEFT': K.Key_Left, 'RIGHT': K.Key_Right, 'PLUS': K.Key_Plus}


def key_from_name(name):
    """'W' / 'F1' / 'Space' / 'Esc' -> a Qt key (K.Key_...). Unknown text gives Key_unknown."""
    name = (name or '').strip()
    if not name:
        return K.Key_unknown
    if name.upper() in _SPECIAL:
        return _SPECIAL[name.upper()]
    k = getattr(K, f'Key_{name.upper()}', None) or getattr(K, f'Key_{name}', None)
    if k is None and len(name) == 1 and name.isdigit():
        k = getattr(K, f'Key_{name}', None)
    return k if k is not None else K.Key_unknown


# keys the player cannot rebind: the window owns F1/F11, and 1-9/0 (plus Alt+1..6) start the games
RESERVED_KEYS = {'F1', 'F11'} | set('0123456789')


def key_name(key):
    """A Qt key -> the short text shown on a button ('W', 'F1', 'Esc', 'Space')."""
    for attr in dir(K):
        if attr.startswith('Key_') and getattr(K, attr) == key:
            name = attr[4:]
            if name.startswith('Unknown') or name.startswith('Sign'):
                return ''
            if name.isdigit():
                return name
            if name == 'Escape':
                return 'Esc'
            if name == 'Return':
                return 'Enter'
            if name == 'Space':
                return 'Space'
            if len(name) == 1:
                return name
            if name[0] == 'F' and name[1:].isdigit():
                return name
            return name.capitalize()
    return ''


class EventDialog(QDialog):
    def __init__(self, parent, ev, state):
        super().__init__(parent)
        self.choice = None
        self.setWindowTitle(tr('Random event'))
        self.setModal(True)
        self.setMinimumWidth(480)
        self.setWindowFlag(Qt.WindowType.WindowCloseButtonHint, False)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 20, 24, 20)
        lay.setSpacing(12)
        lay.addWidget(section(tr('🎲  RANDOM EVENT')))
        lay.addWidget(page_title(ev['title']))
        txt = QLabel(ev['text'])
        txt.setObjectName('prompt')
        txt.setWordWrap(True)
        lay.addWidget(txt)
        for i, (label, enabled, _) in enumerate(ev['choices']):
            b = Button(label)
            b.setMinimumHeight(44)
            if enabled and not enabled(state):
                b.setEnabled(False)
                b.setToolTip(tr('You cannot afford this.'))
            b.clicked.connect(lambda _=False, i=i: self.pick(i))
            lay.addWidget(b)

    def pick(self, i):
        self.choice = i
        self.accept()

    def reject(self):   # you have to decide
        pass


class EndingDialog(QDialog):
    def __init__(self, parent, key, state, meta):
        super().__init__(parent)
        title, kind, text = ENDINGS[key]
        self.start_over = kind == 'bad'
        self.setWindowTitle(tr('Ending'))
        self.setModal(True)
        self.setMinimumWidth(540)
        self.setWindowFlag(Qt.WindowType.WindowCloseButtonHint, False)
        color = {'good': '#4cc38a', 'neutral': '#f4c542', 'bad': '#ff6b6b'}[kind]
        icon = {'good': '🎉', 'neutral': '🎭', 'bad': '💀'}[kind]
        lay = QVBoxLayout(self)
        lay.setContentsMargins(26, 22, 26, 22)
        lay.setSpacing(12)
        tag = QLabel(f'{icon}  ' + tr(kind.upper() + ' ENDING'))   # GOOD ENDING -> İYİ SONUÇ
        tag.setObjectName('section')
        tag.setStyleSheet(f'color:{color};')
        lay.addWidget(tag)
        t = page_title(title)
        t.setStyleSheet(f'color:{color};font-size:28px;')
        lay.addWidget(t)
        body = QLabel(text.format(goal=f'{state.goal:,}'))
        body.setObjectName('prompt')
        body.setWordWrap(True)
        lay.addWidget(body)
        summary = QLabel(
            txf('Day {d}  •  Level {l}  •  Net worth {n} TL  •  Mental health {m}/100', d=state.day,
                l=state.level, n=f'{state.net_worth:,}', m=state.mental) + '\n'
            + txf('Achievements {a}/{b}  •  Endings found {c}/{e}',
                  a=len(meta.achievements), b=len(ACHIEVEMENTS),
                  c=len(meta.endings), e=len(ENDINGS)))
        summary.setObjectName('hint')
        lay.addWidget(summary)
        row = QHBoxLayout()
        if kind != 'bad':
            keep = Button(tr('Keep playing'))
            keep.setObjectName('primary')
            keep.clicked.connect(self.accept)
            row.addWidget(keep)
        new = Button(tr('Start a new game'))
        if kind == 'bad':
            new.setObjectName('primary')
        new.clicked.connect(self.new_game)
        row.addWidget(new)
        lay.addLayout(row)

    def new_game(self):
        self.start_over = True
        self.accept()

    def reject(self):
        pass


class SettingsDialog(QDialog):
    """Display settings. Every change is applied (and saved) immediately."""

    def __init__(self, win):
        super().__init__(win)
        self.win = win
        self.setWindowTitle(tr('Settings'))
        self.setModal(True)
        self.setMinimumWidth(480)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 20, 24, 20)
        lay.setSpacing(12)
        lay.addWidget(page_title(tr('Settings')))
        lay.addWidget(section(tr('DISPLAY')))
        grid = QGridLayout()
        grid.setHorizontalSpacing(18)
        grid.setVerticalSpacing(12)
        self.fs = QCheckBox(tr('Fullscreen  (F11, Esc to leave)'))
        self.theme, self.text, self.anim, self.cards = QComboBox(), QComboBox(), QComboBox(), QComboBox()
        self.lang = QComboBox()                          # D9: interface language
        for k, (name, _) in THEMES.items():
            self.theme.addItem(name, k)
        for k, (name, _) in TEXT_SCALES.items():
            self.text.addItem(name, k)
        for k, (name, _) in ANIM_SPEEDS.items():
            self.anim.addItem(name, k)
        for k, (name, _size) in CARD_SIZES.items():
            self.cards.addItem(f'{name} cards', k)
        for k, name in LANGUAGES.items():
            self.lang.addItem(name, k)
        self.effects = QCheckBox(tr('Visual effects (confetti, floating numbers)'))
        self.sound = QCheckBox(tr('Sound effects (wins, losses, jackpots)'))
        self.log = QCheckBox(tr('Show message log'))
        grid.addWidget(self.fs, 0, 0, 1, 2)
        for row, (label, w) in enumerate(((tr('Theme'), self.theme), (tr('Text size'), self.text),
                                          (tr('Animation speed'), self.anim), (tr('Card size'), self.cards),
                                          (tr('Language'), self.lang)), start=1):
            grid.addWidget(QLabel(label), row, 0)
            grid.addWidget(w, row, 1)
        grid.addWidget(self.effects, 6, 0, 1, 2)
        grid.addWidget(self.sound, 7, 0, 1, 2)
        grid.addWidget(self.log, 8, 0, 1, 2)
        lay.addLayout(grid)
        lay.addWidget(section(tr('KEYBOARD')))
        keys_row = QHBoxLayout()
        keys_btn = Button(tr('Change key bindings...'))
        keys_btn.clicked.connect(self.keybindings)
        self.keys_lbl = QLabel()
        self.keys_lbl.setObjectName('hint')
        self.keys_lbl.setWordWrap(True)
        keys_row.addWidget(keys_btn)
        keys_row.addWidget(self.keys_lbl, 1)
        lay.addLayout(keys_row)
        row = QHBoxLayout()
        restore = Button(tr('Restore defaults'))
        restore.clicked.connect(self.restore)
        close = Button(tr('Close'))
        close.setObjectName('primary')
        close.clicked.connect(self.accept)
        row.addWidget(restore)
        row.addStretch()
        row.addWidget(close)
        lay.addSpacing(6)
        lay.addLayout(row)
        self.load_values()
        for c in (self.fs, self.effects, self.sound, self.log):
            c.toggled.connect(self.changed)
        for c in (self.theme, self.text, self.anim, self.cards, self.lang):
            c.currentIndexChanged.connect(self.changed)

    def load_values(self):
        st = self.win.settings
        widgets = (self.fs, self.effects, self.sound, self.log, self.theme, self.text, self.anim, self.cards,
                   self.lang)
        for w in widgets:
            w.blockSignals(True)
        self.fs.setChecked(st.fullscreen)
        self.effects.setChecked(st.effects)
        self.sound.setChecked(st.sound)
        self.log.setChecked(st.show_log)
        self.theme.setCurrentIndex(self.theme.findData(st.theme))
        self.text.setCurrentIndex(self.text.findData(st.text))
        self.anim.setCurrentIndex(self.anim.findData(st.anim))
        self.cards.setCurrentIndex(self.cards.findData(st.cards))
        self.lang.setCurrentIndex(self.lang.findData(st.lang))
        for w in widgets:
            w.blockSignals(False)
        self.keys_lbl.setText('   '.join(f'{tr(KEY_NAMES[a])}: {k}' for a, k in st.keymap().items()))

    def changed(self, *_):
        st = self.win.settings
        st.fullscreen = self.fs.isChecked()
        st.effects = self.effects.isChecked()
        st.sound = self.sound.isChecked()
        st.show_log = self.log.isChecked()
        st.theme = self.theme.currentData()
        st.text = self.text.currentData()
        st.anim = self.anim.currentData()
        st.cards = self.cards.currentData()
        st.lang = self.lang.currentData()
        self.apply()

    def apply(self):
        """Everything applies live, except the language: rebuilding the window while this dialog
        is open would leave the dialog itself in the old tongue. It is applied on close."""
        if self.win.settings.lang == current():
            self.win.apply_settings()
        else:
            self.win.settings.save()

    def keybindings(self):
        dlg = KeybindDialog(self.win)
        dlg.exec()
        self.apply()                                   # same rule as every other setting
        self.load_values()

    def restore(self):
        self.win.settings.reset()
        self.load_values()
        self.apply()


class KeybindDialog(QDialog):
    """D6: click an action, press a key, done. Esc while capturing cancels the pick."""

    def __init__(self, parent):
        super().__init__(parent)
        self.win = parent
        self.waiting = None
        self.picked = dict(parent.settings.keymap())
        self.setWindowTitle(tr('Key bindings'))
        self.setModal(True)
        self.setMinimumWidth(460)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 20, 24, 20)
        lay.setSpacing(10)
        lay.addWidget(section(tr('KEYBOARD')))
        note = QLabel(tr('Click a button, then press the key you want. The in-game keys (shown on each '
                         'button inside a game) are not affected.'))
        note.setWordWrap(True)
        lay.addWidget(note)
        grid = QGridLayout()
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(8)
        self.btns = {}
        for i, action in enumerate(DEFAULT_KEYS):
            grid.addWidget(QLabel(tr(KEY_NAMES[action])), i // 2, (i % 2) * 2)
            b = Button(self.picked[action])
            b.setMinimumWidth(90)
            b.clicked.connect(lambda _=False, a=action: self.pick(a))
            grid.addWidget(b, i // 2, (i % 2) * 2 + 1)
            self.btns[action] = b
        lay.addLayout(grid)
        row = QHBoxLayout()
        reset = Button(tr('Restore defaults'))
        reset.clicked.connect(self.defaults)
        close = Button(tr('Done'))
        close.setObjectName('primary')
        close.clicked.connect(self.accept)
        row.addWidget(reset)
        row.addStretch()
        row.addWidget(close)
        lay.addLayout(row)

    def pick(self, action):
        self.waiting = action
        self.btns[action].setText(tr('...press a key'))
        for a, b in self.btns.items():
            b.setEnabled(a == action)

    def defaults(self):
        self.picked = dict(DEFAULT_KEYS)
        self.redraw()

    def redraw(self):
        for a, b in self.btns.items():
            b.setText(self.picked[a])
            b.setEnabled(True)

    def keyPressEvent(self, e):
        if self.waiting is None:
            if e.key() == Qt.Key.Key_Escape:
                return self.reject()
            return super().keyPressEvent(e)
        if e.key() == Qt.Key.Key_Escape:                 # change of mind
            self.waiting = None
            self.redraw()
            return
        name = key_name(e.key())
        if name in RESERVED_KEYS:                        # F1/F11 belong to the window, 1-9/0 start the games
            a = self.waiting
            self.waiting = None
            self.redraw()
            self.btns[a].setText(tr('(reserved key)'))
            return
        if name:
            taken = [a for a, k in self.picked.items() if k == name and a != self.waiting]
            used = {name} | {k for a, k in self.picked.items() if a != self.waiting and a not in taken}
            for a in taken:                              # two actions may not share one key: move the loser
                free = next((k for k in DEFAULT_KEYS.values() if k not in used), DEFAULT_KEYS[a])
                self.picked[a] = free
                used.add(free)
            self.picked[self.waiting] = name
        self.waiting = None
        self.redraw()

    def accept(self):
        self.win.settings.set_keymap(self.picked)
        super().accept()


class NewGameDialog(QDialog):
    """Pick a difficulty for a new run. You have to choose."""

    def __init__(self, parent, first_time=False):
        super().__init__(parent)
        self.choice = 'normal'
        self.setWindowTitle(tr('New game'))
        self.setModal(True)
        self.setMinimumWidth(560)
        self.setWindowFlag(Qt.WindowType.WindowCloseButtonHint, False)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(26, 22, 26, 22)
        lay.setSpacing(12)
        lay.addWidget(section(tr('WELCOME') if first_time else tr('NEW GAME')))
        lay.addWidget(page_title(tr('Choose your difficulty')))
        note = QLabel(tr('Your achievements and the endings you have found are kept between games.'))
        note.setWordWrap(True)
        lay.addWidget(note)
        for key, d in DIFFICULTIES.items():
            row = QFrame()
            row.setObjectName('panel')
            hl = QHBoxLayout(row)
            dot = QLabel('●')
            dot.setStyleSheet(f"color:{ {'easy': '#4cc38a', 'normal': '#f4c542', 'hard': '#ff6b6b'}[key] };"
                              'font-size:18px;')
            text = QLabel(f"<b style='font-size:16px'>{tr(d['name'])}</b><br>{d['desc']}")
            text.setWordWrap(True)
            hl.addWidget(dot)
            hl.addWidget(text, 1)
            b = Button(txf('Play {n}', n=tr(d['name'])))
            b.setMinimumWidth(130)
            if key == 'normal':
                b.setObjectName('primary')
            b.clicked.connect(lambda _=False, k=key: self.pick(k))
            hl.addWidget(b)
            lay.addWidget(row)

    def pick(self, key):
        self.choice = key
        self.accept()

    def reject(self):
        pass
