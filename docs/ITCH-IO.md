# itch.io sayfası - yayın kılavuzu

Sayfa metninin tamamı `docs/itch-description.html` dosyasındadır (İngilizce + Türkçe, tek açıklama
alanına yapıştırılır). Bu dosya ayarların, kısa tanıtımların, etiketlerin ve ekran görüntüsü
sırasının listesidir.

## 1. Sayfa ayarları

| Alan | Değer |
|---|---|
| Başlık | `Gamble Game` |
| Kısa tanıtım (EN) | `A casino-life simulation: work, gamble, borrow and try to reach the money goal - or find another way out. 16 games, ~92% RTP, 6 endings, English + Turkish.` (155 karakter) |
| Kısa tanıtım (TR) | `Kumarhane temalı bir hayat simülasyonu: çalış, kumar oyna, borçlan ve para hedefine ulaş - ya da başka bir çıkış bul. 16 oyun, 6 son, Türkçe arayüz.` (148 karakter) |
| Tür (Kind) | Downloadable game |
| Fiyat | **Free** |
| Platform | Windows (hem `.exe` hem `.zip` için işaretle) |
| Durum | Released |
| Website | https://github.com/Undetox57/gamble-game |
| Diğer araç / motor | Python 3 + PyQt6 |
| Girdiler | Klavye, Fare |
| Erişilebilirlik | Tam klavye kontrolü (her eylemin kısayolu var), ayarlanabilir yazı boyutu ve efektler |
| İçerik uyarısı | Listede **Gambling** varsa işaretle; yoksa bu satırı açıklamanın en üstüne ekle: `Fictional gambling with imaginary money - no real money, nothing to buy.` |
| Destek | Ücretsiz; istersen "Say thanks" (bağış) seçeneğini açık bırak |

**Açıklama (Description)**: `docs/itch-description.html` dosyasını tarayıcıda aç → `Ctrl+A` →
`Ctrl+C` → itch.io'nun açıklama kutusuna `Ctrl+V`. Tarayıcı metni zengin metin olarak kopyaladığı
için başlıklar, listeler ve bağlantılar doğru görünür. Türkçe bölüm İngilizcenin altındadır.

## 2. Kapak

`docs/itch-cover.png` (1440x810, 16:9). Lobinin üst kırpımı: başlık, cüzdan, hedef zinciri ve
oyun ızgarası görünüyor.

## 3. Ekran görüntüleri (bu sırayla yükle)

| # | Dosya | Gösterdiği |
|---|---|---|
| 1 | `screenshots/01-lobby.png` | Lobinin tamamı: 16 oyun, hayat eylemleri, solda hedef zinciri |
| 2 | `screenshots/10-lobby-sprint.png` | Turnuva paneli: 10 günlük klasik + 3 günlük sprint, menüde Trofe odası |
| 3 | `screenshots/08b-trophy-plaques.png` | Trofe odası: rekor levhaları (en iyi net varlık, turnuva, sprint, hedef zinciri) |
| 4 | `screenshots/09-goal-chain.png` | Hedef zinciri: 5 basamaktan 4.'sü, sıradaki hedef 1.000.000 TL |
| 5 | `screenshots/07-blackjack.png` | Blackjack eli ortasında |
| 6 | `screenshots/02-keno.png` | Keno turu sonucu |
| 7 | `screenshots/03-statistics.png` | İstatistikler: net varlık grafiği, oyun başına RTP, rekorlar |
| 8 | `screenshots/04-bank-shark.png` | Banka, krediler ve tefeci paneli |
| 9 | `screenshots/08-trophy-room.png` | Trofe vitrini (36 başarı) |
| 10 | `screenshots/05-achievements.png` | Başarılar ve sonlar |
| 11 | `screenshots/06-how-to-play.png` | Nasıl Oynanır: tüm kurallar, ödemeler, kısayollar |
| 12 | `screenshots/01b-tournament.png` | Devam eden klasik turnuva |

Hepsi 1440x1000 PNG. Yeniden üretmek için: `QT_QPA_PLATFORM=windows` altında
`shots.py` (geçici betik) çalıştırılır, kapak `01-lobby.png`'den 16:9 kırpılır:
`python -c "from PIL import Image; im=Image.open('docs/screenshots/01-lobby.png'); im.crop((0,0,im.width,int(im.width*9/16))).save('docs/itch-cover.png')"`

## 4. Etiketler (itch.io'nun otomatik tamamlamasından seç)

İlk beş (sayfada öne çıkanlar): `simulation`, `management`, `casino`, `gambling`, `singleplayer`

Sonrasında eklenebilir: `windows`, `simulator`, `roguelite` (her koşu sıfırdan başlar),
`open source`, `free`, `pyqt`, `text-driven` (metin ağırlıklı olaylar).

## 5. Dosyalar

| Dosya | Ne |
|---|---|
| `GambleGame-1.0.0-Setup.exe` | Kurulum. Yönetici yetkisi istemez, Program Files dışına kurar, kaldırınca kayıtları silmez. |
| `GambleGame-1.0.0-win64.zip` | Taşınabilir. Aç, `GambleGame.exe`'ye çift tıkla (`_internal` klasörünü yanında tut). |

Her ikisine de "Windows" platform etiketi düşer. SHA-256 özetleri `docs/YAYINLAMA.md` ve GitHub
Release notunda; itch.io açıklaması da oraya yönlendiriyor.

## 6. Yayından sonra

- [ ] Sayfa adresini (örn. `https://undetox57.itch.io/gamble-game`) `README.md` içindeki
      "Download (players)" bölümüne ve GitHub Release notuna ekle.
- [ ] itch.io'nun "Download" sayfasında dosya boyutlarının ve platform etiketinin doğru olduğunu
      kontrol et.
- [ ] Kendin bir indirme denemesi yap (Setup.exe + zip): SmartScreen uyarısının açıklamada
      anlatıldığı gibi davrandığını doğrula.
- [ ] Bir devlog yazısı istersen: "How the payout tables are verified with a simulator" - üç
      paragraflık kısa bir yazı, `simulate.py rtp` çıktısıyla birlikte.
