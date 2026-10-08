"""WebP画像の幅と高さを、URLから実測する（構造化データの image の width / height 用。2026-10-09新設）

使い方: python tools/image_size.py https://shira-treat.com/wp-content/uploads/2026/09/image-9-2.webp
出力例: 1202 654
（JPEG・PNGにも対応。ダウンロードはせず先頭の数十KBだけ読む）
"""
import struct
import sys
import urllib.request


def size(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    d = urllib.request.urlopen(req, timeout=20).read()
    if d[:4] == b'RIFF' and d[8:12] == b'WEBP':
        k = d[12:16]
        if k == b'VP8X':
            return 1 + int.from_bytes(d[24:27], 'little'), 1 + int.from_bytes(d[27:30], 'little')
        if k == b'VP8 ':
            w, h = struct.unpack('<HH', d[26:30])
            return w & 0x3fff, h & 0x3fff
        if k == b'VP8L':
            bits = int.from_bytes(d[21:25], 'little')
            return (bits & 0x3fff) + 1, ((bits >> 14) & 0x3fff) + 1
    if d[:8] == b'\x89PNG\r\n\x1a\n':
        return struct.unpack('>II', d[16:24])
    if d[:2] == b'\xff\xd8':
        i = 2
        while i < len(d):
            if d[i] != 0xFF:
                i += 1
                continue
            m = d[i + 1]
            if m in (0xC0, 0xC1, 0xC2):
                h, w = struct.unpack('>HH', d[i + 5:i + 9])
                return w, h
            i += 2 + struct.unpack('>H', d[i + 2:i + 4])[0]
    raise ValueError('画像の形式を判定できません')


if __name__ == '__main__':
    w, h = size(sys.argv[1])
    print(w, h)
