"""Interface language (D9): English and Turkish.

The English text is the key, so `tr('Anything')` in English returns exactly what was written and
the translation table only has to hold the Turkish side. Anything missing from the table falls
back to the English original, which keeps a half-translated build perfectly usable.

The language lives in Settings (`lang=en|tr`), so it survives a restart and old settings files
without the key simply stay English.

Keys fall into two groups:
- literal keys, written as tr('...') / txf('...') in the code;
- runtime keys: game names, category names, difficulty names, achievement and ending texts, job
  and item names - all of them pass through tr() when they are put on screen.
"""

LANGUAGES = {'en': 'English', 'tr': 'Türkçe'}

_lang = 'en'


def set_lang(code):
    """Pick the active language. Unknown codes fall back to English."""
    global _lang
    _lang = code if code in LANGUAGES else 'en'
    return _lang


def current():
    return _lang


def tr(text):
    """English text -> the player's language (identity when the language is English)."""
    if _lang == 'en':
        return text
    return TR.get(_lang, {}).get(text, text)


def txf(template, **kw):
    """tr() + str.format() in one call: txf('Day {n}', n=state.day)."""
    return tr(template).format(**kw)


# ---------------------------------------------------------------------------
# Turkish strings. Keys are the exact English texts used in the UI.
TR = {'tr': {
    # ---- main window / header
    '🎰  GAMBLE GAME': '🎰  KUMARHANE',
    '⚙  Settings': '⚙  Ayarlar',
    '⛶  Fullscreen': '⛶  Tam ekran',
    '⛶  Exit fullscreen': '⛶  Tam ekrandan çık',
    '← Back to lobby': '← Lobiye dön',
    'Welcome to the Gamble Game!': 'Kumarhaneye hoş geldin!',
    'SESSION': 'OTURUM',
    'LEVEL': 'SEVİYE',

    # ---- trophy room (D11)
    '🏆  Trophy room': '🏆  Trofe Odası',
    'Trophy room': 'Trofe Odası',
    'TROPHY CASE  {a}/{b}': 'TROFE VİTRİNİ  {a}/{b}',
    'RECORD PLAQUES': 'REKOR LEVHALARI',
    'Best win this run': 'Bu koşudaki en iyi kazanç',
    'Endings': 'Sonuçlar',
    'Amount:': 'Tutar:',
    'day {d}  •  level {l}': 'gün {d}  •  seviye {l}',

    # ---- result card (D10)
    'Result card': 'Sonuç kartı',
    '📸  Share result card': '📸  Sonuç kartını paylaş',
    '{g} games': '{g} oyun',
    '{w} won, {l} lost': '{w} kazanıldı, {l} kaybedildi',
    'this session': 'bu oturum',
    'Result card saved to {p} - also copied to the clipboard.':
        'Sonuç kartı {p} konumuna kaydedildi - ayrıca panoya da kopyalandı.',
    'Could not share the result card: {e}': 'Sonuç kartı paylaşılamadı: {e}',

    # ---- sidebar
    'WALLET': 'CÜZDAN',
    'Day {n}': '{n}. gün',
    'Bank: {n} TL': 'Banka: {n} TL',
    'Debt: {n} TL': 'Borç: {n} TL',
    'Shark: {n} TL (collects day {d})': 'Tefeci: {n} TL (gün {d}de gelecek)',
    'LEVEL {n}': '{n}. SEVİYE',
    '{n} exp (MAX)': '{n} tp (MAKS)',
    '{a} / {b} exp': '{a} / {b} tp',
    'MENTAL HEALTH': 'RUH SAĞLIĞI',
    'WORK STREAK': 'ÇALIŞMA SERİSİ',
    'GOAL': 'HEDEF',
    '{n} / {g} TL': '{n} / {g} TL',
    'Rung {a}/{b}  •  next {g} TL': 'Basamak {a}/{b}  •  sıradaki {g} TL',
    'Rung {a}/{b}  •  chain complete': 'Basamak {a}/{b}  •  zincir tamamlandı',
    'No Gamble Days: {a}/{b}': 'Kumarsız gün: {a}/{b}',
    'Games today: ': 'Bugün oynanan: ',
    'Skipped days (no games): {n}': 'Geçen günler (oyunsuz): {n}',
    'Clean streaks: {s}   •   Credit limit: {c} TL': 'Temiz seriler: {s}   •   Kredi limiti: {c} TL',
    'Items: ': 'Eşyalar: ',
    'Protected from mental health loss for {n} more day(s).': 'Ruh sağlığı kaybına karşı {n} gün daha korunuyor.',
    'Too tired to work for {n} more day(s).': 'Çalışmak için {n} gün daha çok yorgun.',
    '{n} days worked': '{n} gün çalışıldı',
    'difficulty': 'zorluk',

    # ---- lobby: bet bar
    'Your bet (TL):': 'Bahsiniz (TL):',
    'Min': 'En az',
    'Max': 'En çok',
    'max bet: ': 'en yüksek bahis: ',
    'no limit': 'sınırsız',
    '{n} TL': '{n} TL',

    # ---- lobby: streak side bet
    'STREAK BET': 'SERİ BAHSİ',
    'Stake (TL):': 'Kuruş (TL):',
    '{n} in a row': '{n} art arda',
    'chance': 'şans',
    'CASH OUT THE STREAK BET': 'SERİ BAHİNİ PARALA',
    'RUNNING: {a}/{b} won  •  {s} TL at stake  •  pays {m:g}× = {v} TL  •  a loss in a one-shot game drops it.':
        'SÜRÜYOR: {a}/{b} kazanıldı  •  bahis {s} TL  •  ödemeyi {m:g}× = {v} TL  •  tek seferlik oyun '
        'kaybı seriyi düşürür.',
    'CASH OUT NOW FOR {v} TL  (fair value, no gamble)': 'ŞİMDİ {v} TL’YE PARALA  (gerçek değer, kumarsız)',
    'Win 3, 5, 7 or 10 one-shot games in a row to take the payout. The stake is paid up front and cannot be '
    'refunded. Crash, Mines and Hi-Lo neither count nor break it; a push is neutral.':
        'Ödülü almak için art arda 3, 5, 7 veya 10 tek seferlik oyun kazanın. Kuruş peşin ödenir ve iade '
        'edilmez; Crash, Mines ve Hi-Lo ne sayılır ne bozar; beraberlik nötrtür.',
    'Streak bet not placed: one is already running, or you cannot afford the stake.':
        'Seri bahsi konmadı: zaten bir tane sürüyor ya da kuruşu karşılayamıyorsunuz.',

    # ---- lobby: life & money / menu
    'LIFE & MONEY': 'HAYAT & PARA',
    'Go to Work': 'İşe git',
    'Pass Day': 'Günü geçir',
    'Go out with loved one': 'Sevgiliyle dışarı çık',
    'Bank && Loans': 'Banka && Krediler',
    'Jobs': 'İşler',
    'Shop': 'Dükkân',
    'Statistics': 'İstatistikler',
    'Achievements': 'Başarılar',
    'How to Play': 'Nasıl oynanır',
    'Settings': 'Ayarlar',
    'Reset Game': 'Oyunu sıfırla',
    'Save && Quit': 'Kaydet && Çık',
    'MENU': 'MENÜ',
    'Too tired ({n} day(s))': 'Çok yorgun ({n} gün)',
    'Unlocks at level {n}': '{n}. seviyede açılır',
    'Reset game': 'Oyunu sıfırla',
    'Delete your current run and start over?\n(Achievements and endings are kept.)':
        'Mevcut koşunuz silinsin ve baştan başlansın mı?\n(Başarılar ve sonuçlar korunur.)',
    'Game in progress': 'Oyun sürüyor',
    'Finish the current round before quitting.': 'Çıkmadan önce eli bitirin.',
    'Session summary': 'Oturum özeti',
    'This session': 'Bu oturum',

    # ---- tournament panel
    'TOURNAMENT': 'TURNUVA',
    'Enter tournament': 'Turnuvaya katıl',
    'Tournament running  •  day {a}/{b}': 'Turnuva sürüyor  •  gün {a}/{b}',
    'Enter tournament  •  {e} TL, {d} days': 'Turnuvaya katıl  •  {e} TL, {d} gün',
    'Started day {d} at {n} TL. Now {m} TL ({g} TL). Finish in the black on day {end} to get the {e} TL entry '
    'back, plus {p}% of your growth.':
        '{d}. günde {n} TL ile başladı. Şimdi {m} TL ({g} TL). {end}. gününde artıda bitirirseniz {e} TL '
        'giriş parasını geri alırsınız, üstelik büyümenizin %{p}’si kadar bonus.',
    'A race against your own net worth. The entry is held; finish ahead and you get it back plus {p}% of the '
    'growth (capped), finish behind and it is gone. Best on {diff}: {best}.':
        'Kendi net varlığınıza karşı bir yarış. Giriş parası tutulur; önde bitirirseniz geri alırsınız, üstelik '
        'büyümenizin %{p}’si kadar (üst sınırla); geride bitirirse yanar. {diff} rekoru: {best}.',

    # ---- sprint tournament (D12)
    'Sprint  •  {e} TL, {d} days': 'Sprint  •  {e} TL, {d} gün',
    'Sprint running  •  day {a}/{b}': 'Sprint sürüyor  •  gün {a}/{b}',
    'Sprint: started day {d} at {n} TL. Now {m} TL ({g} TL). Finish in the black on day {end} to get the '
    '{e} TL entry back, plus {p}% of your growth.':
        'Sprint: {d}. günde {n} TL ile başladı. Şimdi {m} TL ({g} TL). {end}. gününde artıda bitirirseniz '
        '{e} TL giriş parasını geri alırsınız, üstelik büyümenizin %{p}’si kadar bonus.',
    'A 3-day dash against your own net worth: {p}% of the growth back on top, capped at {c} TL. Only one '
    'tournament at a time. Best sprint on {diff}: {best}.':
        'Kendi net varlığınıza karşı 3 günlük bir koşu: büyümenizin %{p}’si üstüne eklenir, en fazla '
        '{c} TL. Aynı anda tek turnuva olabilir. {diff} rekoru: {best}.',
    'Best sprint': 'En iyi sprint',
    'Goal chain': 'Hedef zinciri',

    # ---- session / navigation messages
    '{m} min  •  day {d}  •  {g} games': '{m} dk  •  gün {d}  •  {g} oyun',
    '({w} won, {l} lost)': '({w} kazanıldı, {l} kaybedildi)',
    'Best round: +{n} TL': 'En iyi tur: +{n} TL',
    'Net worth this session: {n} TL': 'Bu oturumdaki net varlık: {n} TL',
    'Now: {n} TL': 'Şimdi: {n} TL',
    '{m} min  •  {g} games  ({w} won, {l} lost)  •  best round +{b} TL  •  net worth this session {n} TL':
        '{m} dk  •  {g} oyun  ({w} kazanıldı, {l} kaybedildi)  •  en iyi tur +{b} TL  •  bu oturumdaki net '
        'varlık {n} TL',
    'Finish the hand first - the bet is still on the table.': 'Önce eli bitirin - bahis hâlâ masada.',
    'Invalid bet amount!': 'Geçersiz bahis tutarı!',
    '{n} unlocks at level {l}.': '{n} {l}. seviyede açılır.',
    'The maximum bet at your level is {n:,} TL.': 'Seviyenizde en yüksek bahis {n:,} TL.',

    # ---- bank page
    '🏦  Bank & Loans': '🏦  Banka & Krediler',
    'SAVINGS': 'BIRIKIM',
    'Wallet: {w} TL        Bank: {b} TL': 'Cüzdan: {w} TL        Banka: {b} TL',
    'Your bank balance earns {p}% interest every day (max {m} TL per day at your level).':
        'Banka bakiyeniz her gün %{p} faiz kazanır (seviyenizde gün başına en fazla {m} TL).',
    'Deposit to bank': 'Bankaya yatır',
    'Withdraw from bank': 'Bankadan çek',
    'Withdraw all': 'Hepsini çek',
    'LOANS': 'KREDILER',
    'Debt: {d} TL        Credit available: {c} TL\nCredit limit: {l} TL ({g} TL per level)  •  Interest: {i}% '
    'of your debt every day.':
        'Borç: {d} TL        Kullanılabilir kredi: {c} TL\nKredi limiti: {l} TL (seviye başına {g} TL)  •  '
        'Faiz: her gün borcunuzun %{i}’si.',
    'Borrow': 'Al',
    'Repay': 'Öde',
    'Repay all': 'Hepsini öde',
    'LOAN SHARK  (black money)': 'TEFECİ  (kara para)',
    'Take from the shark': 'Tefeciden al',
    'Pay the shark': 'Tefeciye öde',
    'Pay him everything': 'Hepsini öde',
    'You owe the shark {o} TL.  {r}% interest every day, and he collects {when} (day {d}).\nHe takes {s}% of '
    'your wallet when the day comes ({m} mental health). While you owe him, your wins come back {c}% heavier - '
    'he cleans them for you.':
        'Tefeciye {o} TL borcunuz var.  Günde %{r} faiz, {when} tahsil eder (gün {d}).\nGün gelince '
        'cüzdanınızın %{s}’ini alır ({m} ruh sağlığı). Ona borçluyken kazançlarınız %{c} ağır geri gelir - '
        'sizin için temizler.',
    'No dealings with the shark. He lends up to {l} TL at your level, {r}% a day, collected after {d} days. '
    'While you owe him he cleans {c}% extra out of every win.':
        'Tefeciyle işiniz yok. Seviyenizde en fazla {l} TL verir, günde %{r}, {d} gün sonra tahsil eder. Ona '
        'borçluyken her kazançtan %{c} fazlasını temizler.',
    'today': 'bugün',
    'in {n} day(s)': '{n} gün içinde',

    # ---- jobs page
    '💼  Jobs': '💼  İşler',
    'Better jobs unlock as you level up. Changing jobs resets your work streak.':
        'Seviye atladıkça daha iyi işler açılır. İş değiştirmek çalışma serinizi sıfırlar.',
    '{p} TL/day  •  +{e} exp/day  •  7-day bonus {b} TL  •  stress -{s} mental after 7 days':
        '{p} TL/gün  •  +{e} tp/gün  •  7 günlük prim {b} TL  •  7 günden sonra -{s} ruh sağlığı',
    'Current job': 'Mevcut iş',
    'Take this job': 'Bu işi al',
    'Requires level {n}': '{n}. seviye gerekli',

    # ---- shop page
    '🛒  Shop': '🛒  Dükkân',
    'Wallet: {w} TL        Prices on {d}: {m:.2f}× the normal price':
        'Cüzdan: {w} TL        {d} fiyatları: normalin {m:.2f} katı',
    'Use right away': 'Hemen kullan',
    'Used automatically': 'Otomatik kullanılır',
    'Permanent upgrade': 'Kalıcı yükseltme',
    'In stock: {n}': 'Stokta: {n}',
    'Buy': 'Satın al',
    'Owned': 'Sahipsiniz',
    'You are not tired': 'Yorgun değilsiniz',
    'Not enough money': 'Yeterli para yok',

    # ---- achievements page
    '🏆  Achievements & Endings': '🏆  Başarılar & Sonuçlar',
    'ACHIEVEMENTS  {a}/{b}': 'BAŞARILAR  {a}/{b}',
    'ENDINGS  {a}/{b}': 'SONUÇLAR  {a}/{b}',
    'Achievement': 'Başarı',
    'Description': 'Açıklama',
    'Reward': 'Ödül',
    '+{n} exp': '+{n} tp',
    'Ending': 'Sonuç',
    'Type': 'Tür',
    'GOOD ENDING': 'İYİ SONUÇ',
    'NEUTRAL ENDING': 'NÖTR SONUÇ',
    'BAD ENDING': 'KÖTÜ SONUÇ',
    'Keep playing': 'Oynamaya devam et',
    'Start a new game': 'Yeni oyun başlat',
    'Day {d}  •  Level {l}  •  Net worth {n} TL  •  Mental health {m}/100':
        'Gün {d}  •  Seviye {l}  •  Net varlık {n} TL  •  Ruh sağlığı {m}/100',
    'Achievements {a}/{b}  •  Endings found {c}/{e}':
        'Başarılar {a}/{b}  •  Bulunan sonuçlar {c}/{e}',

    # ---- statistics page
    '📊  Statistics': '📊  İstatistikler',
    'NET WORTH': 'NET VARLIK',
    'DAY': 'GÜN',
    'BEST WIN': 'EN İYİ KAZANÇ',
    'WORST LOSS': 'EN KÖTÜ KAYIP',
    'GAMES PROFIT': 'OYUN KÂRI',
    'DIFFICULTY': 'ZORLUK',
    'NET WORTH OVER TIME': 'ZAMANA GÖRE NET VARLIK',
    'PER-GAME STATS': 'OYUN BAZINDA İSTATİSTİK',
    'Game': 'Oyun',
    'Played': 'Oynanan',
    'Won': 'Kazanılan',
    'Lost': 'Kaybedilen',
    'Win rate': 'Kazanma',
    'Profit': 'Kâr',
    'TOTAL': 'TOPLAM',
    'LAST 20 BETS': 'SON 20 TUR',
    'Result': 'Sonuç',
    'No rounds played yet in this run.': 'Bu koşuda henüz tur oynanmadı.',
    'BEST RUNS  (kept across runs and resets)': 'EN İYİ KOŞULAR  (koşular ve sıfırlamalar arasında saklanır)',
    'Difficulty': 'Zorluk',
    'Best net worth ever': 'En iyi net varlık',
    'This run': 'Bu koşu',
    'Best tournament': 'En iyi turnuva',
    'current': 'seçili',
    'THIS SESSION': 'BU OTURUM',

    # ---- dialogs
    '🎲  RANDOM EVENT': '🎲  RASTGELE OLAY',
    'Random event': 'Rastgele olay',
    'You cannot afford this.': 'Bunu karşılayamazsınız.',
    'New game': 'Yeni oyun',
    'NEW GAME': 'YENİ OYUN',
    'WELCOME': 'HOŞ GELDİNİZ',
    'Choose your difficulty': 'Zorluğunuzu seçin',
    'Your achievements and the endings you have found are kept between games.':
        'Başarılarınız ve bulduğunuz sonuçlar oyunlar arasında korunur.',
    'Play {n}': '{n} oyna',
    'Ayarlar': 'Ayarlar',
    'DISPLAY': 'GÖRÜNTÜ',
    'Theme': 'Tema',
    'Text size': 'Yazı boyutu',
    'Animation speed': 'Animasyon hızı',
    'Card size': 'Kart boyutu',
    'Language': 'Dil',
    'Fullscreen  (F11, Esc to leave)': 'Tam ekran  (F11, çıkmak için Esc)',
    'Visual effects (confetti, floating numbers)': 'Görsel efektler (konfeti, uçan rakamlar)',
    'Sound effects (wins, losses, jackpots)': 'Ses efektleri (kazanç, kayıp, jackpot)',
    'Show message log': 'Mesaj kaydını göster',
    'KEYBOARD': 'KLAVYE',
    'Change key bindings...': 'Kısayolları değiştir...',
    'Restore defaults': 'Varsayılanlara dön',
    'Close': 'Kapat',
    'Key bindings': 'Kısayol tuşları',
    'Click a button, then press the key you want. The in-game keys (shown on each button inside a game) are '
    'not affected.':
        'Önce bir düğmeye tıklayın, sonra istediğiniz tuşa basın. Oyun içi tuşlar (oyundaki düğmelerin '
        'üstünde yazar) etkilenmez.',
    'Done': 'Tamam',
    '...press a key': '...tuşa bas',
    '(reserved key)': '(ayırtılmış tuş)',
    'Cancel': 'Vazgeç',

    # ---- settings key bindings (KEY_NAMES values, looked up at runtime)
    'Go to work': 'İşe git',
    'Pass day': 'Günü geçir',
    'Go out': 'Dışarı çık',
    'Bank & loans': 'Banka & krediler',
    'How to play': 'Nasıl oynanır',

    # ---- game buttons, categories, subtitles (runtime keys)
    'BEGINNER GAMES': 'BAŞLANGIÇ OYUNLARI',
    'ADVANCED GAMES': 'ILERI OYUNLAR',
    'CHANCE GAMES': 'ŞANS OYUNLARI',
    'BETTING GAMES': 'BAHİS OYUNLARI',
    'ARCADE GAMES': 'ARKAD OYUNLARI',
    'Coin Flip': 'Yazı Tura',
    'Dice Roll': 'Zar Atışı',
    'Roulette': 'Rulet',
    'Blackjack': 'Blackjack',
    'Slot Machine': 'Slot Makinesi',
    'Lotto': 'Piyango',
    'Poker': 'Poker',
    'Baccarat': 'Bakara',
    'Race Bet': 'Yarış Bahsi',
    'Wheel of Fortune': 'Şans Çarkı',
    'Scratch Card': 'Kazı Kazan',
    'Crash': 'Crash',
    'Plinko': 'Plinko',
    'Hi-Lo': 'Yüksek-Düşük',
    'Mines': 'Mayınlar',
    'Keno': 'Keno',
    '50/50 • pays 2×': '50/50 • 2× öder',
    'Guess 1-6 • pays 5×': '1-6 tahmin et • 5× öder',
    'Match 3 → 5× • 2 → 1.5×': '3’ü eşleştir → 5× • 2 → 1.5×',
    'Color 2× • number bonus': 'Renk 2× • sayı bonusu',
    'Beat the dealer • 2.5×': 'Kurpiyeyi yen • 2.5×',
    '5-card draw • pays 1.9×': '5 kart çekme • 1.9× öder',
    'Pick 6/30 • up to 2000×': '30’dan 6 seç • 2000×’e kadar',
    'Spin • 0× to 4×': 'Çevir • 0×’den 4×’e',
    'Match 3 • up to 10×': '3’ü eşleştir • 10×’e kadar',
    'Pick the winner • 4×': 'Kazananı seç • 4×',
    'Player vs Banker • 1.9×': 'Oyuncu gegen Banker • 1.9×',
    'Drop a ball • up to 20×': 'Bırak bir top • 20×’e kadar',
    'Cash out in time • no limit': 'Zamanında parala • sınırsız',
    'High or low • × grows each win': 'Yüksek ya da düşük • her kazançta × büyür',
    'Safe cells • cash out anytime': 'Güvenli kareler • istediğin an parala',
    'Pick 10/40 • 3 hits pay, 10 = 20000×': '40’tan 10 seç • 3 tutar öder, 10 = 20000×',

    # ---- difficulties (runtime keys)
    'Easy': 'Kolay',
    'Normal': 'Normal',
    'Hard': 'Zor',
    'Start with 250 TL. Losing costs 3 mental health, loans are cheap, work pays 20% more, the shop is 20% '
    'cheaper and Crash, Mines & Hi-Lo pay back 95%. Goal: 30,000 TL.':
        '250 TL ile başlarsınız. Kaybetmek 3 ruh sağlığı götürür, krediler ucuzdur, iş %20 daha çok öder, '
        'dükkân %20 daha ucuzdur ve Crash, Mines & Hi-Lo %95 geri öder. Hedef: 30.000 TL.',
    'Start with 100 TL. Losing costs 5 mental health, loans cost 3% a day and Crash, Mines & Hi-Lo pay back '
    '92%. Goal: 50,000 TL.':
        '100 TL ile başlarsınız. Kaybetmek 5 ruh sağlığı götürür, krediler günde %3’tür ve Crash, Mines & '
        'Hi-Lo %92 geri öder. Hedef: 50.000 TL.',
    'Start with 50 TL. Losing costs 8 mental health, loans cost 4% a day and are small, work pays 15% less, '
    'the shop is 25% pricier and Crash, Mines & Hi-Lo pay back only 88%. Goal: 100,000 TL.':
        '50 TL ile başlarsınız. Kaybetmek 8 ruh sağlığı götürür, krediler günde %4’tür ve küçüktür, iş %15 '
        'daha az öder, dükkân %25 pahalıdır ve Crash, Mines & Hi-Lo yalnızca %88 geri öder. Hedef: 100.000 TL.',

    # ---- jobs (runtime keys)
    'Delivery Courier': 'Kurye',
    'Cashier': 'Kasiyer',
    'Office Clerk': 'Ofis Elemanı',
    'Accountant': 'Muhasebeci',
    'Manager': 'Müdür',

    # ---- shop items (runtime keys)
    'Therapy Session': 'Terapi Seansı',
    'Restores 25 mental health. Once every 2 days.': '25 ruh sağlığı geri kazandırır. 2 günde bir.',
    'Energy Drink': 'Enerji İçeceği',
    'Removes your work cooldown.': 'İş molanızı kaldırır.',
    'Lucky Charm': 'Uğur Tanesi',
    'Your next win pays 25% extra.': 'Sonraki kazancınız %25 fazla öder.',
    'Loss Insurance': 'Kayıp Sigortası',
    'Your next loss refunds half the bet and costs no mental health.':
        'Sonraki kaybınızda bahsin yarısı iade edilir ve ruh sağlığı götürmez.',
    'Night Classes': 'Gece Kursları',
    '+25% experience from everything.': 'Her şeyden +%25 deneyim.',
    'Pet Cat': 'Evcil Kedi',
    '+2 mental health every new day.': 'Her yeni günde +2 ruh sağlığı.',
    'Comfy Apartment': 'Rahat Daire',
    'Resting (a day without games) restores 15 mental health instead of 10.':
        'Dinlenme (oyunsuz bir gün) 10 yerine 15 ruh sağlığı geri kazandırır.',
    'Used Car': 'İkinci El Araba',
    '+20% pay at work.': 'İşte +%20 ücret.',
    'Financial Advisor': 'Finansal Danışman',
    'Bank interest cap doubled and loan interest 1 point lower.':
        'Faiz üst sınırı iki katına çıkar, kredi faizi 1 puan düşer.',
    'VIP Card': 'VIP Kart',
    'Maximum bet doubled.': 'En yüksek bahis iki katına çıkar.',
    'Second Wind': 'İkinci Rüzgâr',
    'Your next loss costs no mental health and heals 10 instead. No money is refunded.':
        'Sonraki kaybınız ruh sağlığına mal olmaz, bunun yerine 10 iyileştirir. Para iade edilmez.',
    'Streak Notebook': 'Seri Defteri',
    'Shows the live odds of a streak bet and lets you cash it out at its fair value after any win.':
        'Seri bahsinin canlı oranını gösterir ve her kazançtan sonra gerçek değerinden paralamanıza izin verir.',

    # ---- achievements (runtime keys)
    'First Blood': 'İlk Kan',
    'Win your first game.': 'İlk oyununuzu kazanın.',
    'Regular': 'Düzenli',
    'Play 50 games in one run.': 'Tek koşuda 50 oyun oynayın.',
    'Addict?': 'Bağımlı mı?',
    'Play 200 games in one run.': 'Tek koşuda 200 oyun oynayın.',
    'Hot Streak': 'Sıcak Seri',
    'Win 5 games in a row.': 'Art arda 5 oyun kazanın.',
    'Cold Streak': 'Soğuk Seri',
    'Lose 5 games in a row.': 'Art arda 5 oyun kaybedin.',
    'Fortune Favors the Bold': 'Şans Cesurları Sever',
    'Win a game betting your whole wallet.': 'Bütün cüzdanınızı bahse koyup kazanın.',
    'Big Fish': 'Büyük Balık',
    'Win 1,000 TL or more in a single game.': 'Tek oyunda 1.000 TL veya daha fazla kazanın.',
    'Jackpot!': 'Jackpot!',
    'Hit a jackpot (slot, lotto, crash, plinko, mines, hi-lo, keno or scratch).':
        'Jackpot vurun (slot, piyango, crash, plinko, mayın, yüksek-düşük, keno veya kazı kazan).',
    'Natural': 'Doğal',
    'Win with a blackjack from your first two cards.': 'İlk iki kartınızla blackjack yapıp kazanın.',
    'Lucky Numbers': 'Şanslı Sayılar',
    'Match 4 or more numbers in Lotto.': 'Piyangoda 4 veya daha fazla sayı tutturun.',
    'Tried Everything': 'Hepsini Denedim',
    'Play every game at least once in one run.': 'Tek koşuda her oyunu en az bir kez oynayın.',
    'Comfortable': 'Rahat',
    'Reach 1,000 TL net worth.': '1.000 TL net varlığa ulaşın.',
    'Wealthy': 'Varlıklı',
    'Reach 10,000 TL net worth.': '10.000 TL net varlığa ulaşın.',
    'Saver': 'Biriktiren',
    'Have 500 TL in the bank.': 'Bankada 500 TL olsun.',
    'In The Red': 'Kırmızıda',
    'Take out your first loan.': 'İlk kredinizi alın.',
    'Off His List': 'Listesinden Çıktı',
    'Pay the loan shark back in full.': 'Tefeciye borcunuzu tamamen ödeyin.',
    'On The Board': 'Puan Tablosunda',
    'Play a tournament to the end.': 'Bir turnuvayı sonuna kadar oynayın.',
    'Tournament Champion': 'Turnuva Şampiyonu',
    'Set your best tournament result on a difficulty.': 'Bir zorlukta en iyi turnuva sonucunu alın.',
    'Debt Free': 'Borçsuz',
    'Fully repay your debt.': 'Borcunuzu tamamen ödeyin.',
    'Workaholic': 'İşkolik',
    'Complete a 7-day work streak.': '7 günlük çalışma serisi tamamlayın.',
    'Climbing The Ladder': 'Merdiveni Tırmanmak',
    'Get a job as Manager.': 'Müdür olun.',
    'Seasoned': 'Tecrübeli',
    'Reach level 5.': '5. seviyeye ulaşın.',
    'Legend': 'Efsane',
    'Reach level 10.': '10. seviyeye ulaşın.',
    'Clean Streak': 'Temiz Seri',
    'Stay away from gambling for 10 days.': '10 gün kumaraktan uzak durun.',
    'Hanging On': 'Ayakta Kalmak',
    'Survive with 10 or less mental health.': '10 veya daha az ruh sağlığıyla dayanın.',
    'Eventful': 'Olaylı',
    'Make 5 decisions in random events.': 'Rastgele olaylarda 5 karar verin.',
    'Treat Yourself': 'Şımart Kendini',
    'Buy something in the shop.': 'Dükkândan bir şey alın.',
    'Fully Equipped': 'Tam Donanımlı',
    'Own every permanent shop item.': 'Dükkândaki tüm kalıcı eşyalara sahip olun.',
    'Hard Mode, Hard Won': 'Zor Mod, Zor Kazanç',
    'Reach the money goal on Hard difficulty.': 'Zor zorlukta para hedefine ulaşın.',
    'To The Moon': 'Ay’a',
    'Cash out a Crash round at 5× or more.': 'Bir Crash turunu 5× veya daha fazlada paralayın.',
    'Edge Case': 'Köşe Durumu',
    'Land Plinko in a corner slot.': 'Plinko’yu köşe yuvasına düşürün.',
    'Demolition Expert': 'Yıkım Uzmanı',
    'Clear the entire Mines board without touching a mine.':
        'Hiçbir mayına basmadan tüm Mayın tahtasını temizleyin.',
    'Card Sharp': 'Kart Ustası',
    'Win seven Hi-Lo guesses in a row.': 'Art arda yedi Yüksek-Düşük tahmini kazanın.',
    'Whale': 'Balina',
    'Win 5,000 TL or more in a single game.': 'Tek oyunda 5.000 TL veya daha fazla kazanın.',
    'Cold Turkey': 'Kesik Bırakış',
    'Earn the clean-streak reward 3 times (30 clean days).':
        'Temiz seri ödülünü 3 kez kazanın (30 temiz gün).',
    'Sure Thing?': 'Kesin İş mi?',
    'Win a streak side bet.': 'Bir seri yan bahsini kazanın.',

    # ---- endings (runtime keys)
    'Good': 'İyi',
    'Neutral': 'Nötr',
    'Bad': 'Kötü',
    'High Roller': 'Büyük Oyuncu',
    'You reached {goal} TL and walked away with your head on straight. The tables will remember your name, '
    'but you no longer need them.':
        '{goal} TL’ye ulaştınız ve aklınızı yitirmeden ayrıldınız. Masalar adınızı hatırlayacak, ama artık '
        'onlara ihtiyacınız yok.',
    'Hollow Victory': 'Boş Zafer',
    'You hit the money goal, but your mind was long gone. You can afford anything except feeling okay. Maybe '
    'the real jackpot was the sleep you lost along the way.':
        'Para hedefine ulaştınız ama aklınız çoktan gitmişti. Her şeyi alabilirsiniz, sadece kendinizi iyi '
        'hissetmeyi hariç. Belki de asıl jackpot, yol boyunca kaybettiğiniz uykuydu.',
    'Reformed': 'Dönüşen',
    'Three times you stayed away from the tables for ten days straight. Somewhere along the way you stopped '
    'chasing the next bet. Life got quieter, and better.':
        'Üç kez, art arda on gün masalardan uzak kaldınız. Bir yerde bir sonraki bahsi kovalamayı bıraktınız. '
        'Hayat daha sakin, daha iyi oldu.',
    'Breakdown': 'Çöküş',
    'Your mental health hit zero. The lights, the noise, the losses... it all became too much. Time to start '
    'over, and maybe do things differently.':
        'Ruh sağlığınız sıfıra düştü. Işıklar, gürültü, kayıplar... hepsi fazla geldi. Baştan başlama zamanı, '
        'belki de başka türlü.',
    'Bankrupt': 'Iflas',
    'No money, no credit, nothing left to bet. The bank closed its doors to you, and so did the casino.':
        'Para yok, kredi yok, bahse koymak hiçbir şey yok. Banka kapısını yüzünüze kapattı, kumarhane de.',
    'Debt Spiral': 'Borç Sarmalı',
    'The interest grew faster than you could pay it. The calls never stopped, and in the end everything was '
    'taken.':
        'Faiz ödediğinizden hızlı büyüdü. Telefonlar hiç susmadı ve sonunda her şey alındı.',
}}
