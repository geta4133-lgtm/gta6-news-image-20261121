#!/usr/bin/env python3
"""Deterministic PNG infographic generator: THE WORLD IN ONE FRAME.

Pure stdlib (zlib + struct). No network, no randomness, no clock reads.
Output: $MAKEFUN_OUTPUT_DIR/news-image-20261121.png (1560x2040).
"""

import os
import struct
import zlib

W, H = 1560, 2040

# ---------------------------------------------------------------- font
# 5x7 bitmap font, each glyph = 7 rows of 5 bits (MSB = leftmost pixel).
FONT = {
    "A": [0b01110, 0b10001, 0b10001, 0b11111, 0b10001, 0b10001, 0b10001],
    "B": [0b11110, 0b10001, 0b10001, 0b11110, 0b10001, 0b10001, 0b11110],
    "C": [0b01110, 0b10001, 0b10000, 0b10000, 0b10000, 0b10001, 0b01110],
    "D": [0b11110, 0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b11110],
    "E": [0b11111, 0b10000, 0b10000, 0b11110, 0b10000, 0b10000, 0b11111],
    "F": [0b11111, 0b10000, 0b10000, 0b11110, 0b10000, 0b10000, 0b10000],
    "G": [0b01110, 0b10001, 0b10000, 0b10111, 0b10001, 0b10001, 0b01110],
    "H": [0b10001, 0b10001, 0b10001, 0b11111, 0b10001, 0b10001, 0b10001],
    "I": [0b11111, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100, 0b11111],
    "J": [0b00111, 0b00010, 0b00010, 0b00010, 0b00010, 0b10010, 0b01100],
    "K": [0b10001, 0b10010, 0b10100, 0b11000, 0b10100, 0b10010, 0b10001],
    "L": [0b10000, 0b10000, 0b10000, 0b10000, 0b10000, 0b10000, 0b11111],
    "M": [0b10001, 0b11011, 0b10101, 0b10101, 0b10001, 0b10001, 0b10001],
    "N": [0b10001, 0b11001, 0b10101, 0b10011, 0b10001, 0b10001, 0b10001],
    "O": [0b01110, 0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b01110],
    "P": [0b11110, 0b10001, 0b10001, 0b11110, 0b10000, 0b10000, 0b10000],
    "Q": [0b01110, 0b10001, 0b10001, 0b10001, 0b10101, 0b10010, 0b01101],
    "R": [0b11110, 0b10001, 0b10001, 0b11110, 0b10100, 0b10010, 0b10001],
    "S": [0b01111, 0b10000, 0b10000, 0b01110, 0b00001, 0b00001, 0b11110],
    "T": [0b11111, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100],
    "U": [0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b01110],
    "V": [0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b01010, 0b00100],
    "W": [0b10001, 0b10001, 0b10001, 0b10101, 0b10101, 0b11011, 0b10001],
    "X": [0b10001, 0b10001, 0b01010, 0b00100, 0b01010, 0b10001, 0b10001],
    "Y": [0b10001, 0b10001, 0b01010, 0b00100, 0b00100, 0b00100, 0b00100],
    "Z": [0b11111, 0b00001, 0b00010, 0b00100, 0b01000, 0b10000, 0b11111],
    "0": [0b01110, 0b10001, 0b10011, 0b10101, 0b11001, 0b10001, 0b01110],
    "1": [0b00100, 0b01100, 0b00100, 0b00100, 0b00100, 0b00100, 0b01110],
    "2": [0b01110, 0b10001, 0b00001, 0b00110, 0b01000, 0b10000, 0b11111],
    "3": [0b11110, 0b00001, 0b00001, 0b01110, 0b00001, 0b00001, 0b11110],
    "4": [0b00010, 0b00110, 0b01010, 0b10010, 0b11111, 0b00010, 0b00010],
    "5": [0b11111, 0b10000, 0b11110, 0b00001, 0b00001, 0b10001, 0b01110],
    "6": [0b00110, 0b01000, 0b10000, 0b11110, 0b10001, 0b10001, 0b01110],
    "7": [0b11111, 0b00001, 0b00010, 0b00100, 0b01000, 0b01000, 0b01000],
    "8": [0b01110, 0b10001, 0b10001, 0b01110, 0b10001, 0b10001, 0b01110],
    "9": [0b01110, 0b10001, 0b10001, 0b01111, 0b00001, 0b00010, 0b01100],
    " ": [0] * 7,
    "-": [0, 0, 0, 0b11111, 0, 0, 0],
    ".": [0, 0, 0, 0, 0, 0b01100, 0b01100],
    ",": [0, 0, 0, 0, 0b01100, 0b00100, 0b01000],
    ":": [0, 0b01100, 0b01100, 0, 0b01100, 0b01100, 0],
    "!": [0b00100, 0b00100, 0b00100, 0b00100, 0b00100, 0, 0b00100],
    "/": [0b00001, 0b00010, 0b00010, 0b00100, 0b01000, 0b01000, 0b10000],
    "'": [0b00100, 0b00100, 0, 0, 0, 0, 0],
    "(": [0b00010, 0b00100, 0b01000, 0b01000, 0b01000, 0b00100, 0b00010],
    ")": [0b01000, 0b00100, 0b00010, 0b00010, 0b00010, 0b00100, 0b01000],
}

# ---------------------------------------------------------------- colors
BG = (13, 20, 38)          # dark navy
FG = (226, 232, 240)       # near-white text
DIM = (104, 116, 142)      # softer slate so secondary text recedes vs body
RULE = (42, 52, 76)        # subtle divider lines

ACCENTS = [
    (231, 76, 60),    # red     - MIDEAST
    (241, 143, 77),   # orange  - EUROPE ship
    (222, 186, 78),   # amber   - GLOBAL COP31
    (80, 200, 150),   # green   - EUROPE trade
    (155, 110, 220),  # violet  - AMERICAS
    (80, 160, 220),   # blue    - GLOBAL UN
    (60, 220, 200),   # teal    - GLOBAL Mercury
    (220, 130, 170),  # rose    - AFRICA
]

STORIES = [
    ("MIDEAST",  "IRAN STRIKES BAHRAIN AS TANKERS HIT IN HORMUZ"),
    ("EUROPE",   "DRONES SET RUSSIAN CARGO SHIP ABLAZE OFF FINLAND"),
    ("GLOBAL",   "COP31 DEADLOCKED OVER FOSSIL FOSSILS IN OVERTIME"),
    ("EUROPE",   "EU AND INDONESIA SIGN TRADE PACT AFTER 10 YEARS"),
    ("AMERICAS", "MEXICO SEIZES EL CHAPO ISIDRO IN ARMY RAID"),
    ("GLOBAL",   "UN KILLER ROBOT TALKS END WITH NO BINDING TREATY"),
    ("GLOBAL",   "BEPICOLOMBO ENTERS ORBIT AROUND MERCURY"),
    ("AFRICA",   "NIGERIA FUNERAL BOAT TOLL REACHES 24"),
]

# ---------------------------------------------------------------- canvas
PIX = bytearray(BG * (W * H))


def put(x, y, c):
    if 0 <= x < W and 0 <= y < H:
        i = (y * W + x) * 3
        PIX[i:i + 3] = bytes(c)


def rect(x0, y0, x1, y1, c):
    for y in range(max(0, y0), min(H, y1)):
        row = bytes(c) * (min(W, x1) - max(0, x0))
        if row:
            i = (y * W + max(0, x0)) * 3
            PIX[i:i + len(row)] = row


def text(s, x, y, c, scale=3, spacing=1):
    cx = x
    for ch in s.upper():
        rows = FONT.get(ch, FONT[" "])
        for ry, bits in enumerate(rows):
            for rx in range(5):
                if bits & (1 << (4 - rx)):
                    rect(cx + rx * scale, y + ry * scale,
                         cx + rx * scale + scale, y + ry * scale + scale, c)
        cx += (5 + spacing) * scale
    return cx - x


def text_width(s, scale=3, spacing=1):
    return len(s) * (5 + spacing) * scale - spacing * scale


# ---------------------------------------------------------------- pictos
def picto_missile(cx, cy, s, c):
    """Missile: diagonal shaft with fins and a blast dot."""
    for k in range(8):
        rect(cx + k * s, cy - k * s, cx + k * s + s, cy - k * s + s, c)
    rect(cx - s, cy + s, cx + s, cy + 2 * s, c)
    rect(cx + 7 * s, cy - 8 * s, cx + 10 * s, cy - 5 * s, c)


def picto_ship(cx, cy, s, c):
    """Cargo ship: hull plus three container blocks and a flame."""
    rect(cx, cy, cx + 16 * s, cy + 4 * s, c)
    rect(cx + 3 * s, cy - 3 * s, cx + 6 * s, cy, c)
    rect(cx + 7 * s, cy - 5 * s, cx + 10 * s, cy, c)
    rect(cx + 11 * s, cy - 3 * s, cx + 14 * s, cy, c)
    rect(cx + 13 * s, cy - 9 * s, cx + 15 * s, cy - 6 * s, (255, 170, 90))


def picto_globe(cx, cy, s, c):
    """Globe with meridian lines."""
    r = 8 * s
    for dy in range(-r, r + 1):
        half = int((r * r - dy * dy) ** 0.5)
        rect(cx - half, cy + dy, cx + half, cy + dy, c)
    for x in (-4, 0, 4):
        rect(cx + x * s, cy - r, cx + x * s + s, cy + r, BG)
    rect(cx - r, cy - s // 2 - s, cx + r, cy - s // 2, BG)
    rect(cx - r, cy + s // 2, cx + r, cy + s // 2 + s, BG)


def picto_handshake(cx, cy, s, c):
    """Two arrows meeting: trade pact."""
    for k in range(6):
        rect(cx - 14 * s + k * s, cy - k * s, cx - 13 * s + k * s,
             cy - k * s + s, c)
        rect(cx + 14 * s - k * s, cy - k * s, cx + 15 * s - k * s,
             cy - k * s + s, c)
    rect(cx - 4 * s, cy - s, cx + 4 * s, cy + s, c)


def picto_cuffs(cx, cy, s, c):
    """Handcuffs: two rings joined by a bar."""
    for dx, dy in ((-6, 0), (6, 0)):
        r = 5 * s
        for dy2 in range(-r, r + 1):
            half = int((r * r - dy2 * dy2) ** 0.5)
            rect(cx + dx * s - half, cy + dy * s + dy2,
                 cx + dx * s + half, cy + dy * s + dy2, c)
            inner = int(max(0, (r - 2 * s) ** 2 - dy2 * dy2) ** 0.5)
            if inner > 0:
                rect(cx + dx * s - inner, cy + dy * s + dy2,
                     cx + dx * s + inner, cy + dy * s + dy2 + 1, BG)
    rect(cx - 2 * s, cy - s, cx + 2 * s, cy + s, c)


def picto_robot(cx, cy, s, c):
    """Robot head with antenna and crossed eyes (no treaty)."""
    rect(cx - 8 * s, cy - 6 * s, cx + 8 * s, cy + 6 * s, c)
    rect(cx - s, cy - 11 * s, cx + s, cy - 6 * s, c)
    rect(cx - 3 * s, cy - 13 * s, cx + 3 * s, cy - 11 * s, c)
    for ex in (-5, 3):
        rect(cx + ex * s, cy - 2 * s, cx + (ex + 2) * s, cy + 2 * s, BG)
    rect(cx - 4 * s, cy + 3 * s, cx + 4 * s, cy + 4 * s, BG)


def picto_orbit(cx, cy, s, c):
    """Planet with an elliptical orbit ring."""
    r = 6 * s
    for dy in range(-r, r + 1):
        half = int((r * r - dy * dy) ** 0.5)
        rect(cx - half, cy + dy, cx + half, cy + dy, c)
    # orbit: wide flattened ellipse outline
    for t in range(-20, 21):
        x = cx + t * s
        y = cy + int(t * t * s * s // 160) - 2 * s
        if y != cy + int((t - 1) ** 2 * s * s // 160) - 2 * s or abs(t) > 18:
            rect(x - s, y, x + s, y + s, (255, 210, 120))
    rect(cx - 2 * s, cy - 2 * s, cx + s, cy + s, BG)


def picto_boat(cx, cy, s, c):
    """Funeral boat: hull, candle, and waves."""
    for k in range(16):
        rect(cx + k * s, cy + (abs(k - 8)) // 2 * s if k > 3 else cy,
             cx + k * s + s, cy + 4 * s, c)
    rect(cx + 7 * s, cy - 6 * s, cx + 9 * s, cy, (255, 200, 120))
    rect(cx + 6 * s, cy - 8 * s, cx + 10 * s, cy - 6 * s, (255, 160, 90))
    for wx in (0, 6, 12):
        rect(cx + wx * s, cy + 7 * s, cx + (wx + 4) * s, cy + 8 * s, c)


PICTOS = [picto_missile, picto_ship, picto_globe, picto_handshake,
          picto_cuffs, picto_robot, picto_orbit, picto_boat]

TAG_LABEL = {"MIDEAST": "MIDEAST", "EUROPE": "EUROPE", "GLOBAL": "GLOBAL",
             "AMERICAS": "AMERICAS", "AFRICA": "AFRICA"}

# ---------------------------------------------------------------- layout
MARGIN = 70
CARD_TOP = 300
CARD_H = 190
CARD_GAP = 18


def draw_header():
    rect(0, 0, W, 6, ACCENTS[0])
    text("THE WORLD IN ONE FRAME", MARGIN, 78, FG, scale=7)
    text("SATURDAY 21 NOVEMBER 2026", MARGIN, 180, ACCENTS[2], scale=4)
    rect(MARGIN, 252, W - MARGIN, 256, RULE)


def draw_cards():
    y = CARD_TOP
    for idx, (tag, headline) in enumerate(STORIES):
        acc = ACCENTS[idx]
        rect(MARGIN, y, W - MARGIN, y + CARD_H, (24, 32, 54))
        rect(MARGIN, y, MARGIN + 10, y + CARD_H, acc)

        # tag chip
        chip_w = text_width(TAG_LABEL[tag], 3) + 24
        rect(MARGIN + 34, y + 26, MARGIN + 34 + chip_w, y + 56, acc)
        text(tag, MARGIN + 46, y + 33, BG, scale=3)

        # headline (single line, scaled to fit)
        scale = 4
        while text_width(headline, scale) > W - 2 * MARGIN - 90 and scale > 2:
            scale -= 1
        text(headline, MARGIN + 34, y + 100, FG, scale=scale)

        # pictogram in right gutter
        PICTOS[idx](W - MARGIN - 70, y + CARD_H // 2, 3, acc)
        y += CARD_H + CARD_GAP


def draw_footer():
    y = CARD_TOP + 8 * (CARD_H + CARD_GAP)
    rect(MARGIN, y, W - MARGIN, y + 4, RULE)
    text("SOURCES", MARGIN, y + 30, DIM, scale=3)
    text("REUTERS - GUARDIAN - PBS - NYT - AFP", MARGIN, y + 70, DIM, scale=4)
    text("DETERMINISTIC RENDER - NO LIVE DATA", MARGIN, H - 60, DIM, scale=2)


# ---------------------------------------------------------------- png out
def write_png(path):
    raw = bytearray()
    for y in range(H):
        raw.append(0)  # filter type 0
        raw += PIX[y * W * 3:(y + 1) * W * 3]

    def chunk(tag, data):
        c = tag + data
        return (struct.pack(">I", len(data)) + c
                + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF))

    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n")
        f.write(chunk(b"IHDR", ihdr))
        f.write(chunk(b"IDAT", zlib.compress(bytes(raw), 9)))
        f.write(chunk(b"IEND", b""))


def main():
    out_dir = os.environ["MAKEFUN_OUTPUT_DIR"]
    os.makedirs(out_dir, exist_ok=True)
    draw_header()
    draw_cards()
    draw_footer()
    path = os.path.join(out_dir, "news-image-20261121.png")
    write_png(path)
    print("wrote", path)


if __name__ == "__main__":
    main()
