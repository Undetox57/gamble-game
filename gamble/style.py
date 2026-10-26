"""Application stylesheet, colour themes and the persistent display settings."""
import os
import re

from . import config
from .i18n import LANGUAGES

STYLE = """
QWidget { color:#e8eaf0; font-family:'Segoe UI','Inter','Segoe UI Emoji','Helvetica Neue',sans-serif; font-size:14px; }
QMainWindow { background:qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #141821, stop:1 #10131b); }
QMessageBox, QDialog { background:#1c2230; }
QMessageBox QLabel { color:#e8eaf0; }
QLabel { background:transparent; }
#panel { background:qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #232b3d, stop:1 #1c2230); border:1px solid #2a3248; border-radius:12px; }
#felt { background:qradialgradient(cx:0.5, cy:0.3, radius:1.0, stop:0 #16503b, stop:1 #0e3b2c); border:2px solid #1d6b50; border-radius:14px; }
#hairline { background:qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #d4a017, stop:1 #2a3248); border:none; border-radius:1px; }
#appTitle { font-size:24px; font-weight:800; color:#f4c542; letter-spacing:2px; }
#gameTitle { font-size:22px; font-weight:700; color:#f4c542; }
#betTag { font-size:16px; font-weight:700; color:#9ad1ff; }
#section { font-size:12px; font-weight:800; color:#8b93a8; letter-spacing:1px; border-left:3px solid #d4a017; padding-left:8px; }
#bigMoney { font-size:30px; font-weight:800; color:#f4c542; }
#bigDay { font-size:22px; font-weight:800; }
#bank { font-size:16px; color:#9ad1ff; font-weight:600; }
#prompt { font-size:17px; color:#cfe8dc; }
#hint { font-size:12px; color:#9fb8ac; font-weight:700; }
#result { font-size:19px; font-weight:700; background:rgba(0,0,0,0.25); border-radius:10px; padding:8px 14px; }
#status { color:#f4c542; font-size:13px; }
#debt { color:#ff6b6b; font-size:15px; font-weight:700; }
QScrollArea { background:transparent; border:none; }
QScrollArea > QWidget > QWidget { background:transparent; }
QScrollBar:vertical { background:#141821; width:12px; margin:0; }
QScrollBar::handle:vertical { background:#3a4560; border-radius:6px; min-height:30px; }
QScrollBar::handle:vertical:hover { background:#4d5a7d; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height:0; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background:transparent; }
QScrollBar:horizontal { background:#141821; height:12px; margin:0; }
QScrollBar::handle:horizontal { background:#3a4560; border-radius:6px; min-width:30px; }
QScrollBar::handle:horizontal:hover { background:#4d5a7d; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width:0; }
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal { background:transparent; }
#statBig { font-size:22px; font-weight:800; color:#f4c542; }
#statCap { font-size:11px; font-weight:700; color:#8b93a8; letter-spacing:1px; }
#itemName { font-size:16px; font-weight:700; }
#itemDesc { color:#8b93a8; }
QPushButton#headBtn { padding:6px 12px; font-size:13px; }
QComboBox { background:#0f131b; border:1px solid #3a4560; border-radius:8px; padding:6px 10px; min-width:170px; }
QComboBox:hover { border-color:#d4a017; }
QComboBox QAbstractItemView { background:#1c2230; border:1px solid #3a4560; selection-background-color:#d4a017; selection-color:#1a1400; outline:0; }
QCheckBox { spacing:10px; }
QCheckBox:hover { color:#f4c542; }
QCheckBox::indicator { width:18px; height:18px; border-radius:5px; border:2px solid #3a4560; background:#0f131b; }
QCheckBox::indicator:hover { border-color:#d4a017; }
QCheckBox::indicator:checked { background:#d4a017; border-color:#f4c542; }
QPushButton { background:qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #333f5a, stop:1 #2a3348); border:1px solid #3a4560; border-radius:8px; padding:9px 14px; font-weight:600; }
QPushButton:hover { background:qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #3d4a6b, stop:1 #344061); border-color:#4d5a7d; }
QPushButton:pressed { background:#1f2740; }
QPushButton:disabled { background:#1a2030; color:#5a627a; border-color:#252c40; }
QPushButton:checked { background:#d4a017; color:#1a1400; border-color:#f4c542; }
QPushButton#primary { background:qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #f4c542, stop:1 #d4a017); color:#1a1400; border:none; font-size:15px; }
QPushButton#primary:hover { background:#f4c542; }
QPushButton#primary:pressed { background:#d4a017; }
QPushButton#primary:disabled { background:#4a4020; color:#8a8060; }
QPushButton#danger { background:qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #6e2634, stop:1 #5a1f2a); border:1px solid #8a2f3d; }
QPushButton#danger:hover { background:#7a2836; }
QPushButton#gameBtn { text-align:left; padding:12px 14px; font-size:15px; }
QPushButton#num { padding:0; border-radius:6px; }
QSpinBox, QDoubleSpinBox { background:#0f131b; border:1px solid #3a4560; border-radius:8px; padding:6px; font-size:16px;
           font-weight:700; color:#f4c542; }
QSpinBox:hover, QDoubleSpinBox:hover { border-color:#d4a017; }
QProgressBar { background:#0f131b; border:1px solid #2a3248; border-radius:8px; text-align:center; height:18px; color:#e8eaf0; font-weight:600; }
QProgressBar::chunk { background:#4cc38a; border-radius:7px; }
QTextEdit { background:#0f131b; border:1px solid #2a3248; border-radius:10px; padding:4px; selection-background-color:#d4a017; selection-color:#1a1400; }
QTableWidget { background:#0f131b; alternate-background-color:rgba(255,255,255,0.03); gridline-color:#2a3248; border:1px solid #2a3248; border-radius:8px;
        selection-background-color:#3a4560; selection-color:#e8eaf0; }
QHeaderView::section { background:#1c2230; color:#f4c542; padding:6px; border:none; font-weight:700; }
QToolTip { background:#1c2230; color:#e8eaf0; border:1px solid #3a4560; border-radius:6px; padding:6px 8px; font-size:13px; }
"""


BASE_COLORS = {
    'bg': '#141821', 'bg_dark': '#10131b', 'panel': '#1c2230', 'panel_hi': '#232b3d', 'border': '#2a3248',
    'btn': '#2a3348', 'btn_hi': '#333f5a', 'btn_border': '#3a4560',
    'hover': '#344061', 'hover_hi': '#3d4a6b', 'pressed': '#1f2740', 'dis_bg': '#1a2030', 'dis_border': '#252c40',
    'dis_text': '#5a627a', 'input': '#0f131b', 'felt': '#0e3b2c', 'felt_hi': '#16503b', 'felt_border': '#1d6b50',
    'accent_hi': '#f4c542', 'accent': '#d4a017', 'info': '#9ad1ff', 'bar_hover': '#4d5a7d',
    'on_accent': '#1a1400', 'dis_accent_bg': '#4a4020', 'dis_accent_text': '#8a8060', 'muted': '#8b93a8',
    'hint': '#9fb8ac', 'prompt': '#cfe8dc',
}
THEMES = {
    'classic': ('Classic Dark', {}),
    'midnight': ('Midnight Blue', {
        'bg': '#0b1020', 'bg_dark': '#060a14', 'panel': '#121a30', 'panel_hi': '#1a2440', 'border': '#22305a',
        'btn': '#1c2850', 'btn_hi': '#24346a', 'btn_border': '#34457a',
        'hover': '#27366a', 'hover_hi': '#2c3d7a', 'pressed': '#16204a', 'dis_bg': '#101830', 'dis_border': '#1c2850',
        'input': '#080c18', 'felt': '#0d2a4a', 'felt_hi': '#14406b', 'felt_border': '#2a6db0', 'accent_hi': '#5ad1ff',
        'accent': '#2aa7e0', 'info': '#7ecdff', 'on_accent': '#00121f', 'dis_accent_bg': '#173a52',
        'dis_accent_text': '#6a8fa8'}),
    'emerald': ('Emerald', {
        'bg': '#0c1612', 'bg_dark': '#070f0b', 'panel': '#13231c', 'panel_hi': '#1a2e24', 'border': '#21402f',
        'btn': '#1d3528', 'btn_hi': '#254534', 'btn_border': '#34634a',
        'hover': '#2a4d38', 'hover_hi': '#33594a', 'pressed': '#142a1f', 'dis_bg': '#101c16', 'dis_border': '#1b3326',
        'input': '#08110d', 'felt': '#0e4a35', 'felt_hi': '#14664a', 'felt_border': '#2f9a70'}),
    'crimson': ('Crimson Night', {
        'bg': '#150d10', 'bg_dark': '#0d0809', 'panel': '#221419', 'panel_hi': '#2c1a20', 'border': '#3d2029',
        'btn': '#35202a', 'btn_hi': '#432835', 'btn_border': '#5a3040',
        'hover': '#4a2a38', 'hover_hi': '#583446', 'pressed': '#2a1820', 'dis_bg': '#1b1115', 'dis_border': '#2d1a21',
        'input': '#0e080a', 'felt': '#3b0e18', 'felt_hi': '#5c1a28', 'felt_border': '#8a2a40', 'accent_hi': '#ff8a8a',
        'accent': '#e04848', 'info': '#f2a0b0', 'on_accent': '#1a0000', 'dis_accent_bg': '#4a2020',
        'dis_accent_text': '#a07070'}),
    'contrast': ('High Contrast', {
        'bg': '#000000', 'bg_dark': '#000000', 'panel': '#0a0a0a', 'panel_hi': '#141414', 'border': '#ffffff',
        'btn': '#1a1a1a', 'btn_hi': '#262626', 'btn_border': '#ffffff',
        'hover': '#333333', 'hover_hi': '#404040', 'pressed': '#000000', 'dis_bg': '#0a0a0a', 'dis_border': '#666666',
        'dis_text': '#999999', 'input': '#000000', 'felt': '#001a00', 'felt_hi': '#001a00', 'felt_border': '#ffff00',
        'accent_hi': '#ffff00', 'accent': '#ffd400', 'on_accent': '#000000', 'muted': '#dddddd',
        'hint': '#ffffff', 'prompt': '#ffffff'}),
    'royal': ('Royal Purple', {
        'bg': '#160f24', 'bg_dark': '#0e0917', 'panel': '#221736', 'panel_hi': '#2b1e44', 'border': '#3d2c5e',
        'btn': '#33244d', 'btn_hi': '#3f2e60', 'btn_border': '#55407f',
        'hover': '#453268', 'hover_hi': '#513c78', 'pressed': '#251a3a', 'dis_bg': '#1a1330', 'dis_border': '#2c2049',
        'input': '#120c1e', 'felt': '#3a1466', 'felt_hi': '#5a1f96', 'felt_border': '#8b4fd0',
        'info': '#c3a6ff', 'hint': '#b3a6cc', 'prompt': '#e6dcf5', 'muted': '#a294bd', 'bar_hover': '#6a5499'}),
    'neon': ('Neon Night', {
        'bg': '#0a0a12', 'bg_dark': '#05050a', 'panel': '#12121f', 'panel_hi': '#191930', 'border': '#2b2b52',
        'btn': '#1b1b33', 'btn_hi': '#242445', 'btn_border': '#3c3c78',
        'hover': '#2a2a55', 'hover_hi': '#34346a', 'pressed': '#10101f', 'dis_bg': '#0e0e1a', 'dis_border': '#22223f',
        'input': '#07070d', 'felt': '#0b3d3a', 'felt_hi': '#0f5a55', 'felt_border': '#22d3c5',
        'accent_hi': '#ff4fd8', 'accent': '#e038b8', 'info': '#4fffE6', 'on_accent': '#12000e',
        'dis_accent_bg': '#4a1040', 'dis_accent_text': '#c070b0', 'hint': '#7de9df', 'prompt': '#d6fffa'}),
}

# Lobby icons. Purely cosmetic; kept here (Qt-free) so window.py and the game pages can share them.
GAME_ICONS = {'coin': '💰', 'dice': '🎲', 'slot': '🎰', 'roulette': '🎯', 'blackjack': '🃏', 'poker': '🎴',
              'tombala': '🎱', 'wheel': '🎡', 'scratch': '🎟', 'race': '🏇', 'baccarat': '♠', 'plinko': '🔵',
              'crash': '📈', 'hilo': '📇', 'mines': '💣', 'keno': '🔢'}
CATEGORY_ACCENTS = {'BEGINNER GAMES': '#4cc38a', 'ADVANCED GAMES': '#6c8cff', 'CHANCE GAMES': '#b06ee0',
                    'BETTING GAMES': '#ff8a5c', 'ARCADE GAMES': '#3fc8e0'}
TEXT_SCALES = {'small': ('Small', 0.9), 'normal': ('Normal', 1.0), 'large': ('Large', 1.15), 'huge': ('Huge', 1.25)}
ANIM_SPEEDS = {'normal': ('Normal', 1.0), 'fast': ('Fast', 0.5), 'off': ('Instant', 0.0)}
CARD_SIZES = {'small': ('Small', (54, 78)), 'normal': ('Normal', (68, 98)),
              'large': ('Large', (86, 124))}            # D7: how big the playing cards are drawn

# D6: the lobby actions whose hotkey can be changed (the in-game keys stay as printed on the buttons)
DEFAULT_KEYS = {'work': 'W', 'day': 'D', 'out': 'O', 'bank': 'B', 'jobs': 'J', 'shop': 'S',
                'stats': 'T', 'ach': 'A', 'help': 'H', 'settings': 'P'}
KEY_NAMES = {'work': 'Go to work', 'day': 'Pass day', 'out': 'Go out', 'bank': 'Bank & loans',
             'jobs': 'Jobs', 'shop': 'Shop', 'stats': 'Statistics', 'ach': 'Achievements',
             'help': 'How to play', 'settings': 'Settings'}


def build_style(theme='classic', text='normal'):
    """The application stylesheet for a colour theme and a text size."""
    colors = dict(BASE_COLORS)
    colors.update(THEMES.get(theme, THEMES['classic'])[1])
    mapping = {BASE_COLORS[k]: colors[k] for k in BASE_COLORS}
    pattern = re.compile('|'.join(re.escape(h) for h in mapping))
    style = pattern.sub(lambda m: mapping[m.group(0)], STYLE)
    scale = TEXT_SCALES.get(text, TEXT_SCALES['normal'])[1]
    if scale != 1.0:
        style = re.sub(r'font-size:(\d+)px', lambda m: f'font-size:{round(int(m.group(1)) * scale)}px', style)
    return style


class Settings:
    DEFAULTS = {'fullscreen': False, 'theme': 'classic', 'text': 'normal', 'anim': 'normal',
                'effects': True, 'show_log': True, 'help_seen': False,
                'sound': True, 'cards': 'normal', 'keys': '',
                'lang': 'en'}                        # D5 / D7 / D6 / D9 (interface language)

    def __init__(self):
        self.reset()

    def reset(self):
        for k, v in self.DEFAULTS.items():
            setattr(self, k, v)

    def keymap(self):
        """action -> key name, with the defaults for anything missing or garbled in the file."""
        out = dict(DEFAULT_KEYS)
        for one in (self.keys or '').split(','):
            k, sep, v = one.partition('=')
            v = v.strip()
            if sep and k in DEFAULT_KEYS and 1 <= len(v) <= 7:
                out[k] = v.upper() if len(v) == 1 else v      # 'W' vs 'Space' / 'F1' / 'Esc'
        return out

    def set_keymap(self, keymap):
        self.keys = ','.join(f'{k}={v}' for k, v in keymap.items() if v)

    def load(self):
        try:
            if os.path.exists(config.SETTINGS_FILE):
                with open(config.SETTINGS_FILE, 'r', encoding='utf-8') as f:
                    for line in f:
                        k, _, v = line.strip().partition('=')
                        if k in self.DEFAULTS:
                            setattr(self, k, v.lower() == 'true' if isinstance(self.DEFAULTS[k], bool) else v)
        except Exception:
            pass
        if self.theme not in THEMES:
            self.theme = 'classic'
        if self.text not in TEXT_SCALES:
            self.text = 'normal'
        if self.anim not in ANIM_SPEEDS:
            self.anim = 'normal'
        if self.cards not in CARD_SIZES:
            self.cards = 'normal'
        if self.lang not in LANGUAGES:               # old settings files simply have no lang line
            self.lang = 'en'

    def save(self):
        try:
            with open(config.SETTINGS_FILE, 'w', encoding='utf-8') as f:
                for k in self.DEFAULTS:
                    f.write(f'{k}={getattr(self, k)}\n')
        except Exception:
            pass
