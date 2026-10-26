# Dağıtım ve antivirüs rehberi

Bu dosya, oyunu başkalarına verirken ne göndereceğini ve antivirüs yanlış
alarmlarıyla nasıl baş edeceğini anlatır. Hash'leri her yeniden derlemeden
sonra güncelleyin (komutlar en altta).

---

## 1. Ne göndereceğim?

| Durum | Gönderilecek | Not |
|---|---|---|
| Hızlı deneme (tek dosya) | `dist\GambleGame.exe` (35.5 MB) | Tek dosya, çift tıkla açılır. En çok yanlış alarm alan sürüm. |
| **Önerilen** (en temiz) | `dist\GambleGame-1.0.0-win64.zip` (35.5 MB) | Klasör sürümü + `OKUMA-BENIM.txt` + `LICENSE` içerir. |
| **Önerilen** (kurulumlu) | `installer\Output\GambleGame-1.0.0-Setup.exe` (26 MB) | Sihirbaz, kısayol, kaldırma. Yönetici yetkisi istemez. |

Hiçbirinde Python/PyQt6 kurulumu gerekmez.

Zip gönderirken: **zip'i olduğu gibi gönder**, içinden tek dosya çıkarma.
`_internal` klasörü olmadan oyun açılmaz.

---

## 2. Neden antivirüsler sevmiyor?

PyInstaller tek-dosya paketleri, kendini `%TEMP`\`_MEIxxxx` klasörüne açıp
çalıştırdığı için davranışsal olarak "dropper" (dosya açıcı) sınıfına benzer.
İmzasız olduğu için de tarayıcılar şüpheyle yaklaşır.

Bizim yaptıklarımız (bunlar zaten yapıldı):

- [x] Gerçek Windows sürüm bilgisi eklendi (`version_info.txt` → ürün adı, açıklama, telif)
- [x] UPX sıkıştırması kapalı (`upx=False`)
- [x] Klasör (onedir) sürümü üretildi → kendini açmadığı için çok daha az bayrak
- [x] Windows Defender yerel taraması: **tehdit bulunamadı**
- [ ] Kod imzalama (paralı, tek kalıcı çözüm)

Yapılmaması gerekenler: UPX/crypter kullanmak, exe adını tanınan bir programa
("setup.exe", "update.exe") benzetmek, imzayı gizlemek. Bunlar bayrak oranını
**artırır**.

---

## 3. Yanlış alarm bildirimi (ücretsiz, etkili)

### a) Microsoft (Windows Defender) — en önemlisi

<https://www.microsoft.com/wdsi/filesubmission> adresine gidip doldur:

**Submission type:** `File`
**File:** ilgili exe veya zip
**E-posta adresi:** iletişim için
**Uyarı metni (kopyala-yapıştır):**

```
False positive report - Gamble Game (open source game, MIT license)

This is a PyInstaller-packaged open source game. It does not download,
execute or modify anything; it only reads/writes its own save files
(savegame.txt, gamble_meta.txt, gamble_settings.txt) in the folder next to
the executable.

SHA-256:   <hash'i buraya yapıştır>
Size:      <MB> MB
Source:    MIT licensed, full source code included with the distribution

The detection is most likely triggered by the PyInstaller onefile
self-extracting loader. Please whitelist or re-analyse.
```

Aynı sayfadan **folder/zip** de gönderebilirsin.

### b) VirusTotal'a not bırak

<https://www.virustotal.com> → dosyayı yükle → **Comments** sekmesi →
`False positive. Open source (MIT) game built with PyInstaller. Source code:
<repo/link>. SHA-256: <hash>` yaz. Yorumlar satıcılar tarafından okunur.

### c) Diğer satıcılar (aynı metin)

- Avast/AVG: <https://www.avast.com/false-positive-file-form.php>
- Kaspersky: <https://opentip.kaspersky.com/> → sonucun altındaki "Wrong detection"
- ESET: <https://support.eset.com/en/report-false-positive>
- Malwarebytes: <https://www.malwarebytes.com/false-positive>

Genelde 1-7 gün içinde çözülür; imza gerekmez.

### d) Kendi bilgisayarın için hemen çözüm

Windows Security → Virüs ve tehdit koruması → **Dışlamalar** → ekle →
oyunun klasörü. (Sadece senin makineni etkiler.)

### e) Dağıtım biçimini değiştirmek

Zip içindeki exe'ler farklı taranır; zip + okuma dosyası göndermek bayrak
olasılığını düşürür. Kaynağı GitHub'a koyup "kendiniz derleyin" demek de
güven sorununu tamamen çözer.

---

## 4. Kod imzalama (tek kalıcı çözüm, paralı)

- **OV sertifika**: ~70-200 $/yıl, yayına alınması birkaç gün/hafta sürer.
- **EV sertifika**: ~300+ $/yıl, donanım token'ı gerekir, itibar **anında** kazanır.

Aldıktan sonra her iki `.iss`/`.spec` derlemesinin sonunda imzala:

```powershell
signtool sign /fd SHA256 /td SHA256 /tr http://timestamp.digicert.com /a GambleGame.exe
```

---

## 5. Hash'leri güncelleme

```powershell
Get-FileHash dist\GambleGame-1.0.0-win64.zip,
             installer\Output\GambleGame-1.0.0-Setup.exe,
             dist\GambleGame.exe -Algorithm SHA256 |
  ForEach-Object { "{0}  {1}" -f $_.Hash, (Split-Path $_.Path -Leaf) }
```

### Güncel hash'ler (1.0.0)

```
1E7C366B8228C304EBD0BC3BF7DACC610FB6FFE08AC14B0C4344FEF46D94AE94  GambleGame-1.0.0-win64.zip
6F551B68F528B4059DF76E55501A7EF4225B8CC91084209B7381EF6FFC5A3A21  GambleGame-1.0.0-Setup.exe
061931BA240857AEE2CCEF4D45C5F81BBBCEF81F46215C9E5AA254EA7692CC6D  GambleGame.exe (onefile)
F540389B74B59F6638621362995CF01C4AD8C1590F5FAEC5000B4440FE831103  GambleGame\GambleGame.exe (onedir)
```

> Bu dosyada yazan hash'ler **hazırlanan** dosyalara aittir. Oyun kodu
> değişip yeniden derlendiğinde hepsi değişir; bildirim göndermeden önce
> yukarıdaki komutla tazele.

---

## 6. Yeniden üretim

```powershell
# 1) oyun exe'si (klasör sürümü, AV için önerilen)
python -m PyInstaller --noconfirm --clean gamble_gui_onedir.spec
#    tek dosya sürümü istersen:
python -m PyInstaller --noconfirm --clean gamble_gui.spec

# 2) kurulum sihirbazı
& "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer\GambleGame.iss

# 3) zip
Compress-Archive -Path dist\GambleGame -DestinationPath dist\GambleGame-1.0.0-win64.zip -CompressionLevel Optimal
```
