"""Kleiner QR-Code-Erzeuger (Byte-Modus, Fehlerkorrektur M/Q/H/L, Version 1–40) mit SVG-Ausgabe.

Nach dem Verfahren von Project Nayuki „QR Code generator library“ (MIT-Lizenz), stark gekürzt.
Benutzung:  svg = qr_svg("https://…", ecl="M", farbe="#3A1531")
"""

# Fehlerkorrektur: (Format-Bits, Index in den Tabellen)
ECL = {"L": (1, 0), "M": (0, 1), "Q": (3, 2), "H": (2, 3)}
ECC_CODEWORDS_PER_BLOCK = [
    [-1, 7, 10, 15, 20, 26, 18, 20, 24, 30, 18, 20, 24, 26, 30, 22, 24, 28, 30, 28, 28, 28, 28, 30, 30, 26, 28, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30],
    [-1, 10, 16, 26, 18, 24, 16, 18, 22, 22, 26, 30, 22, 22, 24, 24, 28, 28, 26, 26, 26, 26, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28],
    [-1, 13, 22, 18, 26, 18, 24, 18, 22, 20, 24, 28, 26, 24, 20, 30, 24, 28, 28, 26, 30, 28, 30, 30, 30, 30, 28, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30],
    [-1, 17, 28, 22, 16, 22, 28, 26, 26, 24, 28, 24, 28, 22, 24, 24, 30, 28, 28, 26, 28, 30, 24, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30],
]
NUM_ERROR_CORRECTION_BLOCKS = [
    [-1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 4, 4, 4, 4, 4, 6, 6, 6, 6, 7, 8, 8, 9, 9, 10, 12, 12, 12, 13, 14, 15, 16, 17, 18, 19, 19, 20, 21, 22, 24, 25],
    [-1, 1, 1, 1, 2, 2, 4, 4, 4, 5, 5, 5, 8, 9, 9, 10, 10, 11, 13, 14, 16, 17, 17, 18, 20, 21, 23, 25, 26, 28, 29, 31, 33, 35, 37, 38, 40, 43, 45, 47, 49],
    [-1, 1, 1, 2, 2, 4, 4, 6, 6, 8, 8, 8, 10, 12, 16, 12, 17, 16, 18, 21, 20, 23, 23, 25, 27, 29, 34, 34, 35, 38, 40, 43, 45, 48, 51, 53, 56, 59, 62, 65, 68],
    [-1, 1, 1, 2, 4, 4, 4, 5, 6, 8, 8, 11, 11, 16, 16, 18, 16, 19, 21, 25, 25, 25, 34, 30, 32, 35, 37, 40, 42, 45, 48, 51, 54, 57, 60, 63, 66, 70, 74, 77, 81],
]


def _raw_modules(ver):
    r = (16 * ver + 128) * ver + 64
    if ver >= 2:
        n = ver // 7 + 2
        r -= (25 * n - 10) * n - 55
        if ver >= 7:
            r -= 36
    return r


def _data_codewords(ver, e):
    return _raw_modules(ver) // 8 - ECC_CODEWORDS_PER_BLOCK[e][ver] * NUM_ERROR_CORRECTION_BLOCKS[e][ver]


def _rs_mul(x, y):
    z = 0
    for i in reversed(range(8)):
        z = (z << 1) ^ ((z >> 7) * 0x11D)
        z ^= ((y >> i) & 1) * x
    return z


def _rs_divisor(degree):
    r = [0] * (degree - 1) + [1]
    root = 1
    for _ in range(degree):
        for j in range(degree):
            r[j] = _rs_mul(r[j], root)
            if j + 1 < degree:
                r[j] ^= r[j + 1]
        root = _rs_mul(root, 0x02)
    return r


def _rs_remainder(data, div):
    r = [0] * len(div)
    for b in data:
        f = b ^ r.pop(0)
        r.append(0)
        for i, coef in enumerate(div):
            r[i] ^= _rs_mul(coef, f)
    return r


def _alignment_positions(ver):
    if ver == 1:
        return []
    n = ver // 7 + 2
    step = (ver * 8 + n * 3 + 5) // (n * 4 - 4) * 2
    res = [ver * 4 + 10 - i * step for i in range(n - 1)] + [6]
    return list(reversed(res))


class _QR:
    def __init__(self, ver, e_idx, e_bits, codewords, mask=None):
        self.ver, self.size = ver, ver * 4 + 17
        self.e_idx, self.e_bits = e_idx, e_bits
        self.m = [[False] * self.size for _ in range(self.size)]
        self.f = [[False] * self.size for _ in range(self.size)]
        self._function_patterns()
        self._draw_codewords(self._add_ecc(codewords))
        if mask is None:
            best, mask = None, 0
            for i in range(8):
                self._apply_mask(i)
                self._format_bits(i)
                p = self._penalty()
                if best is None or p < best:
                    best, mask = p, i
                self._apply_mask(i)
        self._apply_mask(mask)
        self._format_bits(mask)

    def _set(self, x, y, dark):
        self.m[y][x] = dark
        self.f[y][x] = True

    def _function_patterns(self):
        s = self.size
        for i in range(s):
            self._set(6, i, i % 2 == 0)
            self._set(i, 6, i % 2 == 0)
        for cx, cy in ((3, 3), (s - 4, 3), (3, s - 4)):
            for dy in range(-4, 5):
                for dx in range(-4, 5):
                    x, y = cx + dx, cy + dy
                    if 0 <= x < s and 0 <= y < s:
                        d = max(abs(dx), abs(dy))
                        self._set(x, y, d not in (2, 4))
        pos = _alignment_positions(self.ver)
        n = len(pos)
        for i in range(n):
            for j in range(n):
                if (i == 0 and j == 0) or (i == 0 and j == n - 1) or (i == n - 1 and j == 0):
                    continue
                for dy in range(-2, 3):
                    for dx in range(-2, 3):
                        self._set(pos[i] + dx, pos[j] + dy, max(abs(dx), abs(dy)) != 1)
        self._format_bits(0)
        if self.ver >= 7:
            rem = self.ver
            for _ in range(12):
                rem = (rem << 1) ^ ((rem >> 11) * 0x1F25)
            bits = self.ver << 12 | rem
            for i in range(18):
                bit = (bits >> i) & 1 == 1
                a, b = s - 11 + i % 3, i // 3
                self._set(a, b, bit)
                self._set(b, a, bit)

    def _format_bits(self, mask):
        data = self.e_bits << 3 | mask
        rem = data
        for _ in range(10):
            rem = (rem << 1) ^ ((rem >> 9) * 0x537)
        bits = (data << 10 | rem) ^ 0x5412
        g = lambda i: (bits >> i) & 1 == 1
        for i in range(0, 6):
            self._set(8, i, g(i))
        self._set(8, 7, g(6))
        self._set(8, 8, g(7))
        self._set(7, 8, g(8))
        for i in range(9, 15):
            self._set(14 - i, 8, g(i))
        s = self.size
        for i in range(0, 8):
            self._set(s - 1 - i, 8, g(i))
        for i in range(8, 15):
            self._set(8, s - 15 + i, g(i))
        self._set(8, s - 8, True)

    def _add_ecc(self, data):
        ver, e = self.ver, self.e_idx
        nblocks = NUM_ERROR_CORRECTION_BLOCKS[e][ver]
        ecclen = ECC_CODEWORDS_PER_BLOCK[e][ver]
        raw = _raw_modules(ver) // 8
        nshort = nblocks - raw % nblocks
        shortlen = raw // nblocks
        div = _rs_divisor(ecclen)
        blocks, k = [], 0
        for i in range(nblocks):
            dat = data[k: k + shortlen - ecclen + (0 if i < nshort else 1)]
            k += len(dat)
            ecc = _rs_remainder(dat, div)
            if i < nshort:
                dat = dat + [0]
            blocks.append(dat + ecc)
        res = []
        for i in range(len(blocks[0])):
            for j, blk in enumerate(blocks):
                if i != shortlen - ecclen or j >= nshort:
                    res.append(blk[i])
        return res

    def _draw_codewords(self, data):
        s, i = self.size, 0
        right = s - 1
        while right >= 1:
            if right == 6:
                right = 5
            for vert in range(s):
                for j in range(2):
                    x = right - j
                    upward = ((right + 1) & 2) == 0
                    y = s - 1 - vert if upward else vert
                    if not self.f[y][x] and i < len(data) * 8:
                        self.m[y][x] = (data[i >> 3] >> (7 - (i & 7))) & 1 == 1
                        i += 1
            right -= 2

    def _apply_mask(self, msk):
        fns = [lambda x, y: (x + y) % 2 == 0, lambda x, y: y % 2 == 0, lambda x, y: x % 3 == 0,
               lambda x, y: (x + y) % 3 == 0, lambda x, y: (x // 3 + y // 2) % 2 == 0,
               lambda x, y: x * y % 2 + x * y % 3 == 0, lambda x, y: (x * y % 2 + x * y % 3) % 2 == 0,
               lambda x, y: ((x + y) % 2 + x * y % 3) % 2 == 0]
        f = fns[msk]
        for y in range(self.size):
            for x in range(self.size):
                if not self.f[y][x] and f(x, y):
                    self.m[y][x] = not self.m[y][x]

    def _penalty(self):
        s, m, res = self.size, self.m, 0
        for lines in (m, [list(c) for c in zip(*m)]):
            for row in lines:
                run, prev = 0, None
                for v in row:
                    if v == prev:
                        run += 1
                    else:
                        if run >= 5:
                            res += run - 2
                        run, prev = 1, v
                if run >= 5:
                    res += run - 2
                txt = "".join("1" if v else "0" for v in row)
                for pat in ("10111010000", "00001011101"):
                    res += 40 * sum(1 for i in range(len(txt) - 10) if txt[i:i + 11] == pat)
        for y in range(s - 1):
            for x in range(s - 1):
                c = m[y][x]
                if c == m[y][x + 1] == m[y + 1][x] == m[y + 1][x + 1]:
                    res += 3
        dark = sum(v for row in m for v in row)
        total = s * s
        k = (abs(dark * 20 - total * 10) + total - 1) // total - 1
        return res + k * 10


def qr_matrix(text, ecl="M"):
    e_bits, e_idx = ECL[ecl]
    data = text.encode("utf-8")
    for ver in range(1, 41):
        cap = _data_codewords(ver, e_idx) * 8
        countbits = 8 if ver <= 9 else 16
        used = 4 + countbits + len(data) * 8
        if used <= cap:
            break
    else:
        raise ValueError("Text zu lang für einen QR-Code")
    bits = [0, 1, 0, 0] + [(len(data) >> i) & 1 for i in reversed(range(countbits))]
    for b in data:
        bits += [(b >> i) & 1 for i in reversed(range(8))]
    bits += [0] * min(4, cap - len(bits))
    bits += [0] * ((8 - len(bits) % 8) % 8)
    pad = 0xEC
    while len(bits) < cap:
        bits += [(pad >> i) & 1 for i in reversed(range(8))]
        pad ^= 0xEC ^ 0x11
    words = [int("".join(map(str, bits[i:i + 8])), 2) for i in range(0, len(bits), 8)]
    return _QR(ver, e_idx, e_bits, words).m


def qr_svg(text, ecl="M", farbe="#000", rand=4):
    m = qr_matrix(text, ecl)
    n = len(m) + 2 * rand
    pfad = "".join(f"M{x + rand},{y + rand}h1v1h-1z" for y, row in enumerate(m) for x, v in enumerate(row) if v)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {n} {n}" shape-rendering="crispEdges">'
            f'<rect width="{n}" height="{n}" fill="#fff"/><path d="{pfad}" fill="{farbe}"/></svg>')
