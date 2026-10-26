"""The non-game pages shown in the lobby's stack: bank, jobs, shop, achievements, statistics, how to play."""
import time

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (QAbstractItemView, QFrame, QHBoxLayout, QHeaderView, QLabel, QScrollArea, QSpinBox,
                             QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget)

from . import rules
from .config import (ACHIEVEMENTS, BANK_INTEREST, CLEAN_STREAKS_FOR_ENDING, CLEAN_TARGET, DIFFICULTIES, ENDINGS,
                     GAME_HOTKEYS, GAME_KEYS, GAME_NAMES, GAME_SUBTITLES, ITEMS, JOBS, LEVEL_EXP, LOBBY_ORDER,
                     MAX_BET, SHARK_CLEAN, SHARK_COLLECT_MENTAL, SHARK_COLLECT_SHARE, SHARK_DAYS,
                     SHARK_RATE, STREAK_BETS, STREAK_P_MAX, TENURE_RANKS, TOURNAMENT_BONUS_RATE,
                     TOURNAMENT_DAYS, TOURNAMENT_ENTRY, UNLOCK)
from .style import TEXT_SCALES
from .widgets import AC, Button, LineChart, back_button, clear_layout, page_title, section


def amount_row(*widgets):
    row = QHBoxLayout()
    row.addWidget(QLabel('Amount:'))
    for w in widgets:
        row.addWidget(w)
    row.addStretch()
    return row


def put(table, r, c, text, color=None, align=None):
    it = QTableWidgetItem(str(text))
    if color:
        it.setForeground(QColor(color))
    if align is not None:
        it.setTextAlignment(align)
    table.setItem(r, c, it)


ROW_H = 30          # a table row at the default text size


def fit_height(t, text='normal'):
    """Ask for room for every row - without it the layout squeezes a long table down to one
    visible row (it shrinks to its minimum sizeHint) and the rest of the data is unreachable.
    `text` is the display text size, which makes the rows taller than 30 px."""
    scale = TEXT_SCALES.get(text, TEXT_SCALES['normal'])[1]
    t.setMinimumHeight(round(max(1, t.rowCount()) * ROW_H * scale) + round(46 * scale))
    return t


def make_table(headers, rows):
    t = QTableWidget(rows, len(headers))
    t.setHorizontalHeaderLabels(headers)
    t.verticalHeader().hide()
    t.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    t.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
    t.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    if rows:
        fit_height(t)
    return t


# --------------------------------------------------------------------------- bank
class BankPage(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)
        lay.addWidget(page_title('🏦  Bank & Loans'))
        lay.addWidget(section('SAVINGS'))
        panel = QFrame()
        panel.setObjectName('panel')
        pl = QVBoxLayout(panel)
        pl.setSpacing(10)
        self.info = QLabel()
        self.info.setObjectName('prompt')
        pl.addWidget(self.info)
        self.interest_info = QLabel()
        pl.addWidget(self.interest_info)
        self.dep_spin, self.dep_btn = QSpinBox(), Button('Deposit to bank')
        self.dep_btn.setObjectName('primary')
        self.dep_btn.clicked.connect(lambda: self.act(self.app.engine.deposit, self.dep_spin.value()))
        self.wd_spin, self.wd_btn = QSpinBox(), Button('Withdraw from bank')
        self.wd_btn.clicked.connect(lambda: self.act(self.app.engine.withdraw, self.wd_spin.value()))
        self.wd_all = Button('Withdraw all')
        self.wd_all.clicked.connect(lambda: self.act(self.app.engine.withdraw, int(self.app.state.bank)))
        pl.addLayout(amount_row(self.dep_spin, self.dep_btn))
        pl.addLayout(amount_row(self.wd_spin, self.wd_btn, self.wd_all))
        lay.addWidget(panel)

        lay.addWidget(section('LOANS'))
        loan = QFrame()
        loan.setObjectName('panel')
        ll = QVBoxLayout(loan)
        ll.setSpacing(10)
        self.loan_info = QLabel()
        self.loan_info.setObjectName('prompt')
        self.loan_info.setWordWrap(True)
        ll.addWidget(self.loan_info)
        self.borrow_spin, self.borrow_btn = QSpinBox(), Button('Borrow')
        self.borrow_btn.setObjectName('primary')
        self.borrow_btn.clicked.connect(lambda: self.act(self.app.engine.borrow, self.borrow_spin.value()))
        self.repay_spin, self.repay_btn = QSpinBox(), Button('Repay')
        self.repay_btn.clicked.connect(lambda: self.act(self.app.engine.repay, self.repay_spin.value()))
        self.repay_all = Button('Repay all')
        self.repay_all.clicked.connect(self.do_repay_all)
        ll.addLayout(amount_row(self.borrow_spin, self.borrow_btn))
        ll.addLayout(amount_row(self.repay_spin, self.repay_btn, self.repay_all))
        lay.addWidget(loan)

        lay.addWidget(section('LOAN SHARK  (black money)'))
        shark = QFrame()
        shark.setObjectName('panel')
        sl = QVBoxLayout(shark)
        sl.setSpacing(10)
        self.shark_info = QLabel()
        self.shark_info.setObjectName('prompt')
        self.shark_info.setWordWrap(True)
        sl.addWidget(self.shark_info)
        self.shark_spin, self.shark_btn = QSpinBox(), Button('Take from the shark')
        self.shark_btn.clicked.connect(lambda: self.act(self.app.engine.shark_borrow, self.shark_spin.value()))
        self.shark_pay_spin, self.shark_pay_btn = QSpinBox(), Button('Pay the shark')
        self.shark_pay_btn.setObjectName('primary')
        self.shark_pay_btn.clicked.connect(lambda: self.act(self.app.engine.shark_pay, self.shark_pay_spin.value()))
        self.shark_pay_all = Button('Pay him everything')
        self.shark_pay_all.clicked.connect(self.do_pay_shark_all)
        sl.addLayout(amount_row(self.shark_spin, self.shark_btn))
        sl.addLayout(amount_row(self.shark_pay_spin, self.shark_pay_btn, self.shark_pay_all))
        lay.addWidget(shark)
        lay.addStretch()
        lay.addWidget(back_button(app), 0, Qt.AlignmentFlag.AlignLeft)

    def act(self, fn, amount):
        fn(amount)
        self.app.refresh()

    def do_repay_all(self):
        s = self.app.state
        self.act(self.app.engine.repay, min(s.balance, s.debt))

    def do_pay_shark_all(self):
        s = self.app.state
        self.act(self.app.engine.shark_pay, min(s.balance, s.shark_debt))

    def refresh(self):
        s = self.app.state
        self.info.setText(f'Wallet: {s.balance:,} TL        Bank: {s.bank:,.2f} TL')
        self.interest_info.setText(f'Your bank balance earns {BANK_INTEREST * 100:.0f}% interest every day '
                                   f'(max {s.bank_interest_cap:,} TL per day at your level).')
        self.dep_spin.setRange(1, max(1, min(s.balance, 2_000_000_000)))
        self.dep_btn.setEnabled(s.balance >= 1)
        wmax = int(s.bank)
        self.wd_spin.setRange(1, max(1, min(wmax, 2_000_000_000)))
        self.wd_btn.setEnabled(wmax >= 1)
        self.wd_all.setEnabled(wmax >= 1)
        self.loan_info.setText(
            f'Debt: {s.debt:,} TL        Credit available: {s.credit_available:,} TL\n'
            f'Credit limit: {s.credit_limit:,} TL ({s.diff["credit_per_level"]} TL per level)  •  '
            f'Interest: {s.debt_rate * 100:.0f}% of your debt every day.')
        self.borrow_spin.setRange(1, max(1, min(s.credit_available, 2_000_000_000)))
        self.borrow_btn.setEnabled(s.credit_available >= 1)
        rmax = min(s.balance, s.debt)
        self.repay_spin.setRange(1, max(1, min(rmax, 2_000_000_000)))
        self.repay_btn.setEnabled(rmax >= 1)
        self.repay_all.setEnabled(rmax >= 1)
        owed, room = s.shark_debt, max(0, s.shark_limit - s.shark_debt)
        if owed > 0:
            left = max(0, s.shark_due - s.day)
            self.shark_info.setText(
                f'You owe the shark {owed:,} TL.  {SHARK_RATE * 100:.0f}% interest every day, and he collects '
                f'{"today" if left == 0 else f"in {left} day(s)"} (day {s.shark_due}).\n'
                f'He takes {SHARK_COLLECT_SHARE * 100:.0f}% of your wallet when the day comes '
                f'(-{abs(SHARK_COLLECT_MENTAL)} mental health). While you owe him, your wins come back '
                f'{SHARK_CLEAN * 100:.0f}% heavier - he cleans them for you.')
        else:
            self.shark_info.setText(
                f'No dealings with the shark. He lends up to {s.shark_limit:,} TL at your level, '
                f'{SHARK_RATE * 100:.0f}% a day, collected after {SHARK_DAYS} days. '
                f'While you owe him he cleans {SHARK_CLEAN * 100:.0f}% extra out of every win.')
        self.shark_spin.setRange(1, max(1, min(room, 2_000_000_000)))
        self.shark_btn.setEnabled(room >= 1)
        smax = min(s.balance, s.shark_debt)
        self.shark_pay_spin.setRange(1, max(1, min(smax, 2_000_000_000)))
        self.shark_pay_btn.setEnabled(smax >= 1)
        self.shark_pay_all.setEnabled(smax >= 1)


# --------------------------------------------------------------------------- jobs
class JobsPage(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(page_title('💼  Jobs'))
        lay.addWidget(QLabel('Better jobs unlock as you level up. Changing jobs resets your work streak.'))
        self.rows = QVBoxLayout()
        self.rows.setSpacing(8)
        lay.addLayout(self.rows)
        lay.addStretch()
        lay.addWidget(back_button(app), 0, Qt.AlignmentFlag.AlignLeft)

    def refresh(self):
        s, eng = self.app.state, self.app.engine
        factor = eng.work_factor() * eng.tenure_factor()      # what a shift really pays, as in the sidebar
        clear_layout(self.rows)
        for j in JOBS:
            row = QFrame()
            row.setObjectName('panel')
            hl = QHBoxLayout(row)
            info = QLabel(f"<b style='font-size:16px'>{j['name']}</b><br>"
                          f"{round(j['pay'] * factor)} TL/day  •  +{j['exp']} exp/day  •  "
                          f"7-day bonus {round(j['bonus'] * factor)} TL  •  stress -{j['stress']} mental after 7 days")
            hl.addWidget(info, 1)
            if s.job == j['key']:
                b = Button('Current job')
                b.setEnabled(False)
            elif s.level >= j['level']:
                b = Button('Take this job')
                b.setObjectName('primary')
                b.clicked.connect(lambda _=False, k=j['key']: self.take(k))
            else:
                b = Button(f"Requires level {j['level']}")
                b.setEnabled(False)
            b.setMinimumWidth(150)
            hl.addWidget(b)
            self.rows.addWidget(row)

    def take(self, key):
        self.app.engine.take_job(key)
        self.app.refresh()
        self.refresh()


# --------------------------------------------------------------------------- shop
class ShopPage(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(page_title('🛒  Shop'))
        self.info = QLabel()
        self.info.setObjectName('prompt')
        lay.addWidget(self.info)
        inner = QWidget()
        self.rows = QVBoxLayout(inner)
        self.rows.setContentsMargins(0, 0, 8, 0)
        self.rows.setSpacing(8)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidget(inner)
        lay.addWidget(scroll, 1)
        lay.addWidget(back_button(app), 0, Qt.AlignmentFlag.AlignLeft)

    def refresh(self):
        s, eng = self.app.state, self.app.engine
        self.info.setText(f'Wallet: {s.balance:,} TL        Prices on {s.diff["name"]}: '
                          f'{s.diff["shop_mult"]:.2f}× the normal price')
        clear_layout(self.rows)
        kinds = {'service': 'Use right away', 'consumable': 'Used automatically', 'permanent': 'Permanent upgrade'}
        for item in ITEMS:
            key = item['key']
            row = QFrame()
            row.setObjectName('panel')
            hl = QHBoxLayout(row)
            text = QVBoxLayout()
            name = QLabel(f"{item['name']}   ·   {eng.price(key):,} TL")
            name.setObjectName('itemName')
            desc = QLabel(f"{item['desc']}   ({kinds[item['kind']]})")
            desc.setObjectName('itemDesc')
            desc.setWordWrap(True)
            text.addWidget(name)
            text.addWidget(desc)
            hl.addLayout(text, 1)
            ok, reason = eng.item_status(key)
            stock = s.items.get(key, 0)
            if item['kind'] == 'consumable' and stock:
                hl.addWidget(QLabel(f'In stock: {stock}'))
            b = Button('Buy' if ok else reason)
            b.setEnabled(ok)
            if ok:
                b.setObjectName('primary')
            b.setMinimumWidth(170)
            b.clicked.connect(lambda _=False, k=key: self.buy(k))
            hl.addWidget(b)
            self.rows.addWidget(row)
        self.rows.addStretch()

    def buy(self, key):
        self.app.engine.buy(key)
        self.app.refresh()
        self.refresh()


# --------------------------------------------------------------------------- achievements and endings
class AchievementsPage(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(page_title('🏆  Achievements & Endings'))
        self.ach_label = section('')
        lay.addWidget(self.ach_label)
        self.ach_table = make_table(['', 'Achievement', 'Description', 'Reward'], len(ACHIEVEMENTS))
        self.ach_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        lay.addWidget(self.ach_table, 3)
        self.end_label = section('')
        lay.addWidget(self.end_label)
        self.end_table = make_table(['', 'Ending', 'Type'], len(ENDINGS))
        self.end_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        lay.addWidget(self.end_table, 2)
        lay.addWidget(back_button(app), 0, Qt.AlignmentFlag.AlignLeft)

    def refresh(self):
        meta = self.app.meta
        text = self.app.settings.text
        self.ach_label.setText(f'ACHIEVEMENTS  {len(meta.achievements)}/{len(ACHIEVEMENTS)}')
        for r, (k, title, desc, reward) in enumerate(ACHIEVEMENTS):
            got = k in meta.achievements
            col = '#4cc38a' if got else '#7a8299'
            put(self.ach_table, r, 0, '✓' if got else '·', col)
            put(self.ach_table, r, 1, title, col)
            put(self.ach_table, r, 2, desc, col)
            put(self.ach_table, r, 3, f'+{reward} exp' if reward else '-', col)
        self.end_label.setText(f'ENDINGS  {len(meta.endings)}/{len(ENDINGS)}')
        kinds = {'good': '#4cc38a', 'neutral': '#f4c542', 'bad': '#ff6b6b'}
        for r, (k, (title, kind, _)) in enumerate(ENDINGS.items()):
            if k in meta.endings:
                for c, txt in enumerate(('✓', title, kind.capitalize())):
                    put(self.end_table, r, c, txt, kinds[kind])
            else:
                for c, txt in enumerate(('·', '???', kind.capitalize())):
                    put(self.end_table, r, c, txt, '#7a8299')
        fit_height(self.ach_table, text)
        fit_height(self.end_table, text)


# --------------------------------------------------------------------------- statistics
class StatsPage(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)
        lay.addWidget(page_title('📊  Statistics'))
        cards = QHBoxLayout()
        self.cards = {}
        for key, caption in (('net', 'NET WORTH'), ('day', 'DAY'), ('best', 'BEST WIN'), ('worst', 'WORST LOSS'),
                             ('profit', 'GAMES PROFIT'), ('diff', 'DIFFICULTY')):
            card = QFrame()
            card.setObjectName('panel')
            cl = QVBoxLayout(card)
            cl.setSpacing(0)
            big, cap = QLabel('-'), QLabel(caption)
            big.setObjectName('statBig')
            cap.setObjectName('statCap')
            cl.addWidget(big)
            cl.addWidget(cap)
            cards.addWidget(card)
            self.cards[key] = big
        lay.addLayout(cards)
        lay.addWidget(section('NET WORTH OVER TIME'))
        self.chart = LineChart()
        lay.addWidget(self.chart, 3)
        lay.addWidget(section('PER-GAME STATS'))
        self.table = make_table(['Game', 'Played', 'Won', 'Lost', 'Win rate', 'Profit'], len(GAME_KEYS) + 1)
        lay.addWidget(self.table, 4)
        lay.addWidget(section('LAST 20 BETS'))
        self.bets = make_table(['Game', 'Result'], 0)          # filled in refresh()
        self.bets.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.bets.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        lay.addWidget(self.bets, 2)
        lay.addWidget(section('BEST RUNS  (kept across runs and resets)'))
        self.board = make_table(['Difficulty', 'Best net worth ever', 'This run', 'Best tournament'],
                                len(DIFFICULTIES))
        lay.addWidget(self.board, 0)
        lay.addWidget(section('THIS SESSION'))
        self.session_lbl = QLabel('-')
        self.session_lbl.setWordWrap(True)
        self.session_lbl.setObjectName('itemDesc')
        lay.addWidget(self.session_lbl, 0)
        lay.addWidget(back_button(app), 0, Qt.AlignmentFlag.AlignLeft)

    def refresh(self):
        s = self.app.state
        text = self.app.settings.text                 # row heights follow the display text size
        green, red, gold, muted = '#4cc38a', '#ff6b6b', '#f4c542', '#e8eaf0'
        self.cards['net'].setText(f'{s.net_worth:,}')
        self.cards['day'].setText(str(s.day))
        self.cards['best'].setText(f'+{s.best_win:,}' if s.best_win else '-')
        self.cards['worst'].setText(f'{s.worst_loss:,}' if s.worst_loss else '-')
        total_profit = sum(s.profit.values())
        self.cards['profit'].setText(f'{total_profit:+,}')
        self.cards['diff'].setText(s.diff['name'])
        self.cards['best'].setStyleSheet(f'color:{green};' if s.best_win else f'color:{muted};')
        self.cards['worst'].setStyleSheet(f'color:{red};' if s.worst_loss else f'color:{muted};')
        self.cards['profit'].setStyleSheet(
            f'color:{green};' if total_profit > 0 else f'color:{red};' if total_profit < 0 else f'color:{muted};')
        self.cards['net'].setStyleSheet(f'color:{gold};')
        self.chart.set_data(s.history + [(s.day, s.net_worth)] if s.history[-1][0] != s.day else s.history, s.goal)
        tp = tw = tl = 0
        rows = []
        for k in GAME_KEYS:
            st = s.stats[k]
            rows.append((GAME_NAMES[k], st['played'], st['won'], st['lost'], s.profit.get(k, 0)))
            tp, tw, tl = tp + st['played'], tw + st['won'], tl + st['lost']
        rows.append(('TOTAL', tp, tw, tl, total_profit))
        for r, (name, p, w, l, prof) in enumerate(rows):
            rate = f'{w / p * 100:.0f}%' if p else '-'
            color = '#4cc38a' if prof > 0 else '#ff6b6b' if prof < 0 else None
            for c, val in enumerate((name, p, w, l, rate, f'{prof:+,}' if p else '-')):
                put(self.table, r, c, val, color if c == 5 else None,
                    AC if c else Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                if r == len(rows) - 1:
                    it = self.table.item(r, c)
                    f = it.font()
                    f.setBold(True)
                    it.setFont(f)
        # the last rounds, newest first - what has been happening to the wallet lately
        bets = s.bet_history[-20:]
        self.bets.setRowCount(max(1, len(bets)))
        fit_height(self.bets, text)                    # the row count changes here, not at build time
        fit_height(self.table, text)                   # taller rows when the display text is enlarged
        fit_height(self.board, text)
        if not bets:
            put(self.bets, 0, 0, 'No rounds played yet in this run.', None,
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            put(self.bets, 0, 1, '-')
        for r, (k, d) in enumerate(reversed(bets)):
            color = green if d > 0 else red if d < 0 else muted
            put(self.bets, r, 0, GAME_NAMES.get(k, k), None,
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            put(self.bets, r, 1, f'{d:+,}', color, AC)
        # per-difficulty records from the meta file: the best wallet ever seen on each difficulty
        records = getattr(self.app.meta, 'records', {})
        tours = getattr(self.app.meta, 'tournaments', {})
        for r, key in enumerate(DIFFICULTIES):
            best, mine = records.get(key, 0), key == s.difficulty
            put(self.board, r, 0, DIFFICULTIES[key]['name'] + ('  ◀ current' if mine else ''), gold if mine else None,
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            put(self.board, r, 1, f'{best:,}' if best else '-', gold if best else muted, AC)
            put(self.board, r, 2, f'{s.net_worth:,}' if mine else '-', muted if mine else None, AC)
            tour = tours.get(key, 0)
            put(self.board, r, 3, f'{tour:+,}' if tour else '-', gold if tour else muted, AC)
        ses = getattr(self.app, 'session', None)
        if ses:
            minutes = max(0, round((time.time() - ses['start']) / 60))
            self.session_lbl.setText(
                f'{minutes} min  •  {ses["games"]} games  ({ses["wins"]} won, '
                f'{ses["games"] - ses["wins"]} lost)  •  best round +{ses["best"]:,} TL  •  net worth this '
                f'session {s.net_worth - ses["net0"]:+,} TL')


# --------------------------------------------------------------------------- how to play
def help_html(state):
    gold = '#f4c542'
    h = lambda t: f"<h3 style='color:{gold};margin-top:16px;margin-bottom:2px'>{t}</h3>"   # noqa: E731
    edge = state.diff['edge']

    def rtp_cell(k):                                  # D8: what each game gives back on average
        if k == 'plinko':                             # the only one that depends on your risk choice
            lo, hi = rules.plinko_rtp('low'), rules.plinko_rtp('high')
            return f'{min(lo, hi) * 100:.0f}–{max(lo, hi) * 100:.0f}%'
        note = rules.RTP_NOTES.get(k, '')
        return f'{rules.game_rtp(k, edge) * 100:.0f}%' + (f"<br><i style='font-size:11px'>{note}</i>" if note else '')

    games = ''.join(
        f"<tr><td><b>{GAME_NAMES[k]}</b></td><td>level {UNLOCK[k]}</td><td>{GAME_SUBTITLES[k]}</td>"
        f"<td>{rtp_cell(k)}</td><td>{GAME_HOTKEYS[k]}</td></tr>" for k in LOBBY_ORDER)
    streaks = ''.join(
        f"<tr><td>{n} in a row</td><td>{m:g}×</td><td>{STREAK_P_MAX ** n * 100:.1f}%</td>"
        f"<td>{int(100 * m * STREAK_P_MAX ** n):,} TL per 100 TL stake</td></tr>"
        for n, m in sorted(STREAK_BETS.items()))
    levels = ''.join(
        f"<tr><td>{i + 1}</td><td>{e:,} exp</td><td>{'no limit' if MAX_BET[i] >= 10 ** 9 else f'{MAX_BET[i]:,} TL'}</td></tr>"
        for i, e in enumerate(LEVEL_EXP))
    jobs = ''.join(f"<tr><td><b>{j['name']}</b></td><td>level {j['level']}</td><td>{j['pay']} TL/day</td>"
                   f"<td>7-day bonus {j['bonus']} TL</td></tr>" for j in JOBS)
    items = ''.join(f"<li><b>{i['name']}</b> ({i['price']} TL, level {i['level']}): {i['desc']}</li>" for i in ITEMS)
    diffs = ''.join(f"<li><b>{d['name']}</b>: {d['desc']}</li>" for d in DIFFICULTIES.values())
    return f"""
<h2 style='color:{gold}'>How to play</h2>
<p>You are broke, a little reckless and one lucky streak away from a different life. Your goal is to reach a net
worth of <b>{state.goal:,} TL</b> (wallet + bank − debt − loan-shark debt) on <b>{state.diff['name']}</b>
difficulty. Or find another way out; there are six endings.</p>
{h('A day in your life')}
<ul>
<li><b>Games:</b> every game you play uses part of your day. After 5 games the day ends.</li>
<li><b>Work:</b> go to work for money and experience. Work 7 days in a row for a bonus, but it tires you (3 days off).
If you gamble in the middle of a streak, your boss resets it.</li>
<li><b>Pass Day:</b> do nothing. If you played no games that day you rest and recover mental health.</li>
<li><b>Mental health:</b> every loss costs some. At 0 it is over. Going out with your loved one (100 TL) protects
you from this for 7 days.</li>
<li><b>{CLEAN_TARGET} days without gambling</b> give a willpower reward. Do it {CLEAN_STREAKS_FOR_ENDING} times (after you have
gambled a bit) and you may find a different ending.</li>
</ul>
{h('Games, levels and shortcuts')}
<p>Games unlock as you level up (exp comes from playing, working, achievements and events). The maximum bet grows with your level.
Almost every game pays back less than you put in (roughly 80-95%), so the house wins in the long run; only the coin
flip is fair. Skill matters in Blackjack, Poker, Crash and in your risk choices.</p>
<p>The <b>RTP</b> column is exactly that: how many TL a game gives back per 100 TL wagered, averaged over
forever. Crash, Mines and Hi-Lo follow the difficulty ({state.diff['name']} pays {(1 - edge) * 100:.0f}%), everything
else pays the same everywhere. On Easy those three pay back 95%, on Normal 92%, on Hard 88%.</p>
<table cellspacing='6'><tr><td><i>Game</i></td><td><i>Unlocks</i></td><td><i>Payout</i></td><td><i>RTP</i></td><td><i>Key</i></td></tr>{games}</table>
{h('Levels')}
<table cellspacing='6'><tr><td><i>Level</i></td><td><i>Needs</i></td><td><i>Max bet</i></td></tr>{levels}</table>
{h('Jobs')}
<table cellspacing='6'>{jobs}</table>
<p>Every shift counts as <b>tenure</b>: each rank (New Hire → Company Legend) pays 5% more for the rest of the run,
and your current rank is shown under your job in the side panel.</p>
{h('Bank and loans')}
<p>Savings earn {BANK_INTEREST * 100:.0f}% a day (capped by your level). Loans are limited by your level and cost
{state.diff['debt_rate'] * 100:.0f}% a day on {state.diff['name']}. If your debt grows past your credit limit it hurts your mental health,
and if it grows far past it, you lose everything.</p>
{h('Loan shark')}
<p>On the bank page there is a second door: the <b>loan shark</b>. No credit check, no paperwork - he lends
{SHARK_RATE * 100:.0f}% a day (the bank's rate is nothing by comparison), up to {state.shark_limit:,} TL at your level,
and he gives you exactly {SHARK_DAYS} days. When the day comes he takes {SHARK_COLLECT_SHARE * 100:.0f}% of whatever is in
your wallet and costs you {abs(SHARK_COLLECT_MENTAL)} mental health, then {SHARK_DAYS} more days are added to the clock.
The one favour he does you: while you owe him, he cleans black money for free, so every win pays
{SHARK_CLEAN * 100:.0f}% extra. Owe him three times your ceiling and that is the end of the run.</p>
{h('Tournament')}
<p>The <b>Tournament</b> panel in the lobby runs a {TOURNAMENT_DAYS}-day race against <b>your own net worth</b>:
you pay a {TOURNAMENT_ENTRY:,} TL entry fee up front and it is held for the whole window, so it never counts
against your score. Finish at a higher net worth than you started and the entry comes back plus
{TOURNAMENT_BONUS_RATE * 100:.0f}% of your growth (capped); finish behind and the fee is gone. Only one
tournament can run at a time, and the best result of every difficulty is kept in <b>Statistics</b> across
runs and resets.</p>
{h('Shop')}
<ul>{items}</ul>
{h('Random events')}
<p>Most new days bring nothing, some bring a decision. There is no perfect answer, only trade-offs.</p>
{h('Difficulty')}
<ul>{diffs}</ul>
{h('Streak bet')}
<p>From the lobby you may side-bet that you will win several one-shot games in a row. The stake is paid when you
place it and is not refunded; only one-shot games count (Crash, Mines and Hi-Lo neither count nor break it, and a
push is neutral). A loss breaks the run.</p>
<table cellspacing='6'><tr><td><i>Target</i></td><td><i>Pays</i></td><td><i>Chance*</i></td>
<td><i>Expected return</i></td></tr>{streaks}</table>
<p><i>*best case, playing the safest side every time. The game is priced about 8% against you, the same as the table
games. The Streak Notebook (shop) shows these odds live and lets you cash a running bet out at its fair value.</i></p>
{h('Keyboard')}
<ul>
<li><b>Lobby:</b> the game keys above, <b>W</b> work, <b>D</b> pass day, <b>O</b> go out, <b>B</b> bank, <b>J</b> jobs,
<b>S</b> shop, <b>T</b> statistics, <b>A</b> achievements, <b>P</b> settings, <b>H</b> or <b>F1</b> this page.
These lobby keys can be changed in <b>Settings → Change key bindings</b>; the buttons show the current keys.</li>
<li><b>In a game:</b> the key is written on each button. <b>Space</b> usually does the main thing
(spin, stand, draw, cash out, play again).</li>
<li><b>Esc</b> goes back. <b>F11</b> toggles fullscreen. Click the bet box to type a bet; press Enter when done.</li>
</ul>
{h('Tips')}
<ul>
<li>Work and the shop are how you grow. Gambling is how you lose it, or occasionally win big.</li>
<li>Borrowed money is only worth it for something that pays back more than {state.diff['debt_rate'] * 100:.0f}% a day.</li>
<li>Your achievements and the endings you have found are kept when you start a new game.</li>
</ul>
"""


class HelpPage(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        self.text = QLabel()
        self.text.setTextFormat(Qt.TextFormat.RichText)
        self.text.setWordWrap(True)
        self.text.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.text.setContentsMargins(4, 0, 12, 0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidget(self.text)
        lay.addWidget(scroll, 1)
        lay.addWidget(back_button(app), 0, Qt.AlignmentFlag.AlignLeft)

    def refresh(self):
        self.text.setText(help_html(self.app.state))
