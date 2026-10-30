"""installer/GambleGame.ico üretir - oyunun pencere ikonuyla birebir aynı çip (D14).

Kullanım:  python tools\make_icon.py
Çıktı:     installer\GambleGame.ico

Spec dosyaları (gamble_gui.spec / gamble_gui_onedir.spec) ve Inno Setup kurulumu bu .ico dosyasını
kullanır; dosya repoda durur, yalnızca ikon tasarımını değiştirirsen yeniden üret. ICO kabı PNG
sıkıştırması kabul eder (Vista+), yani Qt ile çizilen pikseller doğrudan paketlenir.
"""
import os
import struct
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from PyQt6.QtCore import QBuffer, QIODevice, QSize                     # noqa: E402
from PyQt6.QtWidgets import QApplication                                # noqa: E402

from gamble.widgets import app_icon                                     # noqa: E402

SIZES = (16, 24, 32, 48, 64, 128, 256)
OUT = os.path.join(ROOT, 'installer', 'GambleGame.ico')


def main():
    app = QApplication.instance() or QApplication([])
    icon = app_icon()
    entries, blobs = [], b''
    offset = 6 + 16 * len(SIZES)                    # ICO header + one 16-byte entry per size
    for s in SIZES:
        buf = QBuffer()
        buf.open(QIODevice.OpenModeFlag.WriteOnly)
        icon.pixmap(QSize(s, s)).save(buf, 'PNG')
        data = bytes(buf.data())
        entries.append(struct.pack('<BBBBHHII', s % 256, s % 256, 0, 0, 1, 32, len(data), offset))
        blobs += data
        offset += len(data)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, 'wb') as f:
        f.write(struct.pack('<HHH', 0, 1, len(SIZES)) + b''.join(entries) + blobs)
    print(f'{OUT} written ({os.path.getsize(OUT)} bytes, sizes {SIZES})')


if __name__ == '__main__':
    main()
