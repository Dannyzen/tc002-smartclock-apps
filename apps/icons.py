"""Generate 16x16 pixel-art GIF icons for AWTRIX NG TC002 using pure Python.

Icons Generated:
  - candle.gif (animated flickering Shabbat candles)
  - cake.gif (animated birthday cake with flickering flame)
  - basketball.gif (NBA basketball with black seams)

No external libraries (PIL/Pillow) required. Uses pure standard library struct/bytes.
"""

import struct
from pathlib import Path


def write_gif89a(filename, width, height, frames, palette, delay=25):
    """Write an animated or static GIF89a file from raw pixel indices and RGB palette."""
    pal_len = 1
    while pal_len < len(palette):
        pal_len *= 2
    pal_len = max(pal_len, 2)
    palette_padded = list(palette)
    while len(palette_padded) < pal_len:
        palette_padded.append((0, 0, 0))

    color_res = pal_len.bit_length() - 1
    gct_flag = 0x80 | ((color_res - 1) << 4) | (color_res - 1)

    out = bytearray()
    # Header & Logical Screen Descriptor
    out.extend(b"GIF89a")
    out.extend(struct.pack("<HHBBB", width, height, gct_flag, 0, 0))

    # Global Color Table
    for r, g, b in palette_padded:
        out.extend(struct.pack("BBB", r, g, b))

    # Netscape loop extension for animation
    if len(frames) > 1:
        out.extend(
            b"\x21\xff\x0b\x4e\x45\x54\x53\x43\x41\x50\x45\x32\x2e\x30\x03\x01\x00\x00\x00"
        )

    for frame in frames:
        # Graphics Control Extension (transparent index 0, delay in 1/100s)
        out.extend(struct.pack("<BBBBHBB", 0x21, 0xF9, 4, 0x09, delay, 0, 0))
        # Image Descriptor
        out.extend(struct.pack("<BHHHHB", 0x2C, 0, 0, width, height, 0x00))

        min_code_size = max(2, color_res)
        clear_code = 1 << min_code_size
        eoi_code = clear_code + 1

        def lzw_encode(pixels, min_size, clear_code=clear_code, eoi_code=eoi_code):
            code_size = min_size + 1
            max_code = 1 << code_size
            table = {bytes([i]): i for i in range(1 << min_size)}
            next_code = eoi_code + 1

            bits = 0
            bit_buf = 0
            encoded_bytes = bytearray()

            def emit(code):
                nonlocal bits, bit_buf, encoded_bytes
                bit_buf |= code << bits
                bits += code_size
                while bits >= 8:
                    encoded_bytes.append(bit_buf & 0xFF)
                    bit_buf >>= 8
                    bits -= 8

            emit(clear_code)
            buf = bytes([pixels[0]])
            for p in pixels[1:]:
                c = bytes([p])
                if buf + c in table:
                    buf = buf + c
                else:
                    emit(table[buf])
                    if next_code < 4096:
                        table[buf + c] = next_code
                        next_code += 1
                        if next_code > max_code and code_size < 12:
                            code_size += 1
                            max_code = 1 << code_size
                    else:
                        emit(clear_code)
                        table = {bytes([i]): i for i in range(1 << min_size)}
                        next_code = eoi_code + 1
                        code_size = min_size + 1
                        max_code = 1 << code_size
                    buf = c
            if buf:
                emit(table[buf])
            emit(eoi_code)
            if bits > 0:
                encoded_bytes.append(bit_buf & 0xFF)

            res = bytearray([min_size])
            idx = 0
            while idx < len(encoded_bytes):
                chunk = encoded_bytes[idx : idx + 255]
                res.append(len(chunk))
                res.extend(chunk)
                idx += len(chunk)
            res.append(0)
            return res

        out.extend(lzw_encode(frame, min_code_size))

    out.append(0x3B)
    Path(filename).parent.mkdir(parents=True, exist_ok=True)
    with open(filename, "wb") as f:
        f.write(out)
    print(f"Generated {filename} ({len(out)} bytes)")


def generate_candle_gif(output_path):
    """Generate 16x16 animated Shabbat candles icon."""
    palette = [
        (0, 0, 0),  # 0: transparent
        (255, 255, 255),  # 1: candle body white
        (255, 235, 59),  # 2: flame yellow
        (255, 112, 67),  # 3: flame orange
        (207, 216, 220),  # 4: candlestick silver
        (144, 164, 174),  # 5: shadow silver
    ]

    def make_frame(flicker):
        g = [[0] * 16 for _ in range(16)]
        for y in range(7, 14):
            g[y][3] = 4
            g[y][4] = 1
            g[y][5] = 5
        g[14][2] = 4
        g[14][3] = 4
        g[14][4] = 4
        g[14][5] = 4
        g[14][6] = 5

        for y in range(7, 14):
            g[y][10] = 4
            g[y][11] = 1
            g[y][12] = 5
        g[14][9] = 4
        g[14][10] = 4
        g[14][11] = 4
        g[14][12] = 4
        g[14][13] = 5

        g[6][4] = 3
        g[6][11] = 3

        if not flicker:
            g[2][4] = 2
            g[3][4] = 2
            g[3][3] = 3
            g[4][4] = 3
            g[5][4] = 3
            g[2][11] = 2
            g[3][11] = 2
            g[3][12] = 3
            g[4][11] = 3
            g[5][11] = 3
        else:
            g[2][3] = 2
            g[3][4] = 2
            g[3][5] = 3
            g[4][4] = 3
            g[5][4] = 3
            g[2][12] = 2
            g[3][11] = 2
            g[3][10] = 3
            g[4][11] = 3
            g[5][11] = 3

        return [px for row in g for px in row]

    write_gif89a(
        output_path, 16, 16, [make_frame(False), make_frame(True)], palette, delay=25
    )


def generate_cake_gif(output_path):
    """Generate 16x16 animated birthday cake icon."""
    palette = [
        (0, 0, 0),  # 0: transparent
        (255, 255, 255),  # 1: white frosting
        (240, 98, 146),  # 2: pink frosting
        (141, 110, 99),  # 3: chocolate sponge
        (255, 238, 88),  # 4: yellow flame
        (255, 112, 67),  # 5: orange flame
        (66, 165, 245),  # 6: cyan candle
        (176, 190, 197),  # 7: plate
    ]

    def make_frame(flicker):
        g = [[0] * 16 for _ in range(16)]
        for x in range(2, 14):
            g[14][x] = 7
        for y in (12, 13):
            for x in range(3, 13):
                g[y][x] = 3
        for x in range(3, 13):
            g[11][x] = 4
        for y in (9, 10):
            for x in range(3, 13):
                g[y][x] = 2
        for x in range(3, 13):
            g[8][x] = 1
        g[9][4] = 1
        g[9][7] = 1
        g[9][11] = 1
        for y in (5, 6, 7):
            g[y][7] = 6
            g[y][8] = 1

        if not flicker:
            g[2][7] = 4
            g[3][7] = 5
            g[3][8] = 4
            g[4][7] = 5
        else:
            g[2][8] = 4
            g[3][8] = 5
            g[3][7] = 4
            g[4][8] = 5

        return [px for row in g for px in row]

    write_gif89a(
        output_path, 16, 16, [make_frame(False), make_frame(True)], palette, delay=25
    )


def generate_basketball_gif(output_path):
    """Generate 16x16 basketball icon with black seams."""
    palette = [
        (0, 0, 0),  # 0: transparent
        (230, 81, 0),  # 1: dark orange shadow
        (255, 112, 67),  # 2: bright orange body
        (255, 171, 145),  # 3: highlight orange
        (33, 33, 33),  # 4: black seams
    ]

    g = [[0] * 16 for _ in range(16)]
    for y in range(16):
        for x in range(16):
            dx = x - 7.5
            dy = y - 7.5
            dist_sq = dx * dx + dy * dy
            if dist_sq <= 38:
                if dist_sq >= 32:
                    g[y][x] = 1
                elif dx < -1 and dy < -1:
                    g[y][x] = 3
                else:
                    g[y][x] = 2

    for y in range(2, 14):
        g[y][7] = 4
    for x in range(2, 14):
        g[7][x] = 4

    for x, y in [(4, 4), (4, 5), (4, 9), (4, 10), (5, 6), (5, 7), (5, 8)]:
        if g[y][x] != 0:
            g[y][x] = 4
    for x, y in [(11, 4), (11, 5), (11, 9), (11, 10), (10, 6), (10, 7), (10, 8)]:
        if g[y][x] != 0:
            g[y][x] = 4

    pixels = [px for row in g for px in row]
    write_gif89a(output_path, 16, 16, [pixels], palette, delay=100)


def main():
    root = Path(__file__).resolve().parents[1]
    icons_dir = root / "icons"
    generate_candle_gif(icons_dir / "candle.gif")
    generate_cake_gif(icons_dir / "cake.gif")
    generate_basketball_gif(icons_dir / "basketball.gif")
    print("All icons successfully generated in:", icons_dir)


if __name__ == "__main__":
    main()
