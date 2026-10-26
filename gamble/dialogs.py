"""Modal dialogs: random events, endings, settings, key bindings and the new-game difficulty picker."""
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QCheckBox, QComboBox, QDialog, QFrame, QGridLayout, QHBoxLayout, QLabel, QVBoxLayout

from .config import ACHIEVEMENTS, DIFFICULTIES, ENDINGS
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
        self.setWindowTitle('Random event')
        self.setModal(True)
        self.setMinimumWidth(480)
        self.setWindowFlag(Qt.WindowType.WindowCloseButtonHint, False)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 20, 24, 20)
        lay.setSpacing(12)
        lay.addWidget(section('🎲  RANDOM EVENT'))
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
                b.setToolTip('You cannot afford this.')
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
        self.setWindowTitle('Ending')
        self.setModal(True)
        self.setMinimumWidth(540)
        self.setWindowFlag(Qt.WindowType.WindowCloseButtonHint, False)
        color = {'good': '#4cc38a', 'neutral': '#f4c542', 'bad': '#ff6b6b'}[kind]
        icon = {'good': '🎉', 'neutral': '🎭', 'bad': '💀'}[kind]
        lay = QVBoxLayout(self)
        lay.setContentsMargins(26, 22, 26, 22)
        lay.setSpacing(12)
        tag = QLabel(f'{icon}  {kind.upper()} ENDING')
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
        summary = QLabel(f'Day {state.day}  •  Level {state.level}  •  Net worth {state.net_worth:,} TL  •  '
                         f'Mental health {state.mental}/100\n'
                         f'Achievements {len(meta.achievements)}/{len(ACHIEVEMENTS)}  •  '
                         f'Endings found {len(meta.endings)}/{len(ENDINGS)}')
        summary.setObjectName('hint')
        lay.addWidget(summary)
        row = QHBoxLayout()
        if kind != 'bad':
            keep = Button('Keep playing')
            keep.setObjectName('primary')
            keep.clicked.connect(self.accept)
            row.addWidget(keep)
        new = Button('Start a new game')
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
        self.setWindowTitle('Settings')
        self.setModal(True)
        self.setMinimumWidth(480)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 20, 24, 20)
        lay.setSpacing(12)
        lay.addWidget(page_title('Settings'))
        lay.addWidget(section('DISPLAY'))
        grid = QGridLayout()
        grid.setHorizontalSpacing(18)
        grid.setVerticalSpacing(12)
        self.fs = QCheckBox('Fullscreen  (F11, Esc to leave)')
        self.theme, self.text, self.anim, self.cards = QComboBox(), QComboBox(), QComboBox(), QComboBox()
        for k, (name, _) in THEMES.items():
            self.theme.addItem(name, k)
        for k, (name, _) in TEXT_SCALES.items():
            self.text.addItem(name, k)
        for k, (name, _) in ANIM_SPEEDS.items():
            self.anim.addItem(name, k)
        for k, (name, _size) in CARD_SIZES.items():
            self.cards.addItem(f'{name} cards', k)
        self.effects = QCheckBox('Visual effects (confetti, floating numbers)')
        self.sound = QCheckBox('Sound effects (wins, losses, jackpots)')
        self.log = QCheckBox('Show message log')
        grid.addWidget(self.fs, 0, 0, 1, 2)
        for row, (label, w) in enumerate((('Theme', self.theme), ('Text size', self.text),
                                          ('Animation speed', self.anim), ('Card size', self.cards)), start=1):
            grid.addWidget(QLabel(label), row, 0)
            grid.addWidget(w, row, 1)
        grid.addWidget(self.effects, 5, 0, 1, 2)
        grid.addWidget(self.sound, 6, 0, 1, 2)
        grid.addWidget(self.log, 7, 0, 1, 2)
        lay.addLayout(grid)
        lay.addWidget(section('KEYBOARD'))
        keys_row = QHBoxLayout()
        keys_btn = Button('Change key bindings...')
        keys_btn.clicked.connect(self.keybindings)
        self.keys_lbl = QLabel()
        self.keys_lbl.setObjectName('hint')
        self.keys_lbl.setWordWrap(True)
        keys_row.addWidget(keys_btn)
        keys_row.addWidget(self.keys_lbl, 1)
        lay.addLayout(keys_row)
        row = QHBoxLayout()
        restore = Button('Restore defaults')
        restore.clicked.connect(self.restore)
        close = Button('Close')
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
        for c in (self.theme, self.text, self.anim, self.cards):
            c.currentIndexChanged.connect(self.changed)

    def load_values(self):
        st = self.win.settings
        widgets = (self.fs, self.effects, self.sound, self.log, self.theme, self.text, self.anim, self.cards)
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
        for w in widgets:
            w.blockSignals(False)
        self.keys_lbl.setText('   '.join(f'{KEY_NAMES[a]}: {k}' for a, k in st.keymap().items()))

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
        self.win.apply_settings()

    def keybindings(self):
        dlg = KeybindDialog(self.win)
        dlg.exec()
        self.win.apply_settings()
        self.load_values()

    def restore(self):
        self.win.settings.reset()
        self.load_values()
        self.win.apply_settings()


class KeybindDialog(QDialog):
    """D6: click an action, press a key, done. Esc while capturing cancels the pick."""

    def __init__(self, parent):
        super().__init__(parent)
        self.win = parent
        self.waiting = None
        self.picked = dict(parent.settings.keymap())
        self.setWindowTitle('Key bindings')
        self.setModal(True)
        self.setMinimumWidth(460)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 20, 24, 20)
        lay.setSpacing(10)
        lay.addWidget(section('KEYBOARD'))
        note = QLabel('Click a button, then press the key you want. The in-game keys (shown on each '
                      'button inside a game) are not affected.')
        note.setWordWrap(True)
        lay.addWidget(note)
        grid = QGridLayout()
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(8)
        self.btns = {}
        for i, action in enumerate(DEFAULT_KEYS):
            grid.addWidget(QLabel(KEY_NAMES[action]), i // 2, (i % 2) * 2)
            b = Button(self.picked[action])
            b.setMinimumWidth(90)
            b.clicked.connect(lambda _=False, a=action: self.pick(a))
            grid.addWidget(b, i // 2, (i % 2) * 2 + 1)
            self.btns[action] = b
        lay.addLayout(grid)
        row = QHBoxLayout()
        reset = Button('Restore defaults')
        reset.clicked.connect(self.defaults)
        close = Button('Done')
        close.setObjectName('primary')
        close.clicked.connect(self.accept)
        row.addWidget(reset)
        row.addStretch()
        row.addWidget(close)
        lay.addLayout(row)

    def pick(self, action):
        self.waiting = action
        self.btns[action].setText('...press a key')
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
        if name:
            taken = [a for a, k in self.picked.items() if k == name and a != self.waiting]
            for a in taken:                              # two actions may not share one key
                self.picked[a] = DEFAULT_KEYS[a]
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
        self.setWindowTitle('New game')
        self.setModal(True)
        self.setMinimumWidth(560)
        self.setWindowFlag(Qt.WindowType.WindowCloseButtonHint, False)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(26, 22, 26, 22)
        lay.setSpacing(12)
        lay.addWidget(section('WELCOME' if first_time else 'NEW GAME'))
        lay.addWidget(page_title('Choose your difficulty'))
        note = QLabel('Your achievements and the endings you have found are kept between games.')
        note.setWordWrap(True)
        lay.addWidget(note)
        for key, d in DIFFICULTIES.items():
            row = QFrame()
            row.setObjectName('panel')
            hl = QHBoxLayout(row)
            dot = QLabel('●')
            dot.setStyleSheet(f"color:{ {'easy': '#4cc38a', 'normal': '#f4c542', 'hard': '#ff6b6b'}[key] };"
                              'font-size:18px;')
            text = QLabel(f"<b style='font-size:16px'>{d['name']}</b><br>{d['desc']}")
            text.setWordWrap(True)
            hl.addWidget(dot)
            hl.addWidget(text, 1)
            b = Button(f"Play {d['name']}")
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
