import os
import sys

BRAILLE_BASE = 0x2800
DOTS = ((0x01, 0x08), (0x02, 0x10), (0x04, 0x20), (0x40, 0x80))

COLOR_MODE = 'auto'

ANSI16_TABLE = [
    (0, 0, 0), (128, 0, 0), (0, 128, 0), (128, 128, 0),
    (0, 0, 128), (128, 0, 128), (0, 128, 128), (192, 192, 192),
    (128, 128, 128), (255, 0, 0), (0, 255, 0), (255, 255, 0),
    (0, 0, 255), (255, 0, 255), (0, 255, 255), (255, 255, 255),
]

def _closest_ansi16(r, g, b):
    best = 7
    best_dist = float('inf')
    for i, (cr, cg, cb) in enumerate(ANSI16_TABLE):
        d = (r - cr) ** 2 + (g - cg) ** 2 + (b - cb) ** 2
        if d < best_dist:
            best_dist = d
            best = i
    if best < 8:
        return f'\033[{30 + best}m'
    return f'\033[{90 + best - 8}m'

def _closest_ansi16_bg(r, g, b):
    best = 0
    best_dist = float('inf')
    for i, (cr, cg, cb) in enumerate(ANSI16_TABLE):
        d = (r - cr) ** 2 + (g - cg) ** 2 + (b - cb) ** 2
        if d < best_dist:
            best_dist = d
            best = i
    if best < 8:
        return f'\033[{40 + best}m'
    return f'\033[{100 + best - 8}m'

def _rgb_to_256(r, g, b):
    if r == g == b:
        if r < 8:
            return 16
        if r > 248:
            return 231
        return round((r - 8) / 247 * 24) + 232
    return 16 + 36 * round(r / 255 * 5) + 6 * round(g / 255 * 5) + round(b / 255 * 5)

def _detect_color_mode():
    ct = os.environ.get('COLORTERM', '').lower()
    if ct in ('truecolor', '24bit'):
        return 'truecolor'
    term = os.environ.get('TERM', '').lower()
    if '256color' in term:
        return '256'
    if term:
        return '16'
    return 'truecolor'

def _ansi_fg(r, g, b, mode=None):
    if mode is None:
        mode = COLOR_MODE
    if mode == 'auto':
        mode = _detect_color_mode()
    if mode == 'none':
        return ''
    if mode == '16':
        return _closest_ansi16(r, g, b)
    if mode == '256':
        return f'\033[38;5;{_rgb_to_256(r, g, b)}m'
    return f'\033[38;2;{r};{g};{b}m'

def _ansi_bg(r, g, b, mode=None):
    if mode is None:
        mode = COLOR_MODE
    if mode == 'auto':
        mode = _detect_color_mode()
    if mode == 'none':
        return ''
    if mode == '16':
        return _closest_ansi16_bg(r, g, b)
    if mode == '256':
        return f'\033[48;5;{_rgb_to_256(r, g, b)}m'
    return f'\033[48;2;{r};{g};{b}m'


class BrailleCanvas:
    def __init__(self, width, height):
        self.cols = (width + 1) // 2
        self.rows = (height + 3) // 4
        self.width = self.cols * 2
        self.height = self.rows * 4
        self.pixels = set()
        self.pixel_color = {}
        self.text_color = {}
        self.texts = []
        self.bg_color = None

    def clear(self):
        self.pixels.clear()
        self.pixel_color.clear()
        self.text_color.clear()
        self.texts.clear()

    def set_pixel(self, x, y, color=None):
        x, y = int(x), int(y)
        if 0 <= x < self.width and 0 <= y < self.height:
            self.pixels.add((x, y))
            if color:
                cell = (x // 2, y // 4)
                self.pixel_color[cell] = color

    def _bresenham(self, x1, y1, x2, y2):
        x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
        points = []
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx - dy
        while True:
            points.append((x1, y1))
            if x1 == x2 and y1 == y2:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x1 += sx
            if e2 < dx:
                err += dx
                y1 += sy
        return points

    def _brush(self, x, y, radius, color):
        if radius <= 0:
            self.set_pixel(x, y, color)
        else:
            for dy in range(-radius, radius + 1):
                for dx in range(-radius, radius + 1):
                    if dx * dx + dy * dy <= radius * radius:
                        self.set_pixel(x + dx, y + dy, color)

    def draw_line(self, x1, y1, x2, y2, color=None, width=1):
        points = self._bresenham(x1, y1, x2, y2)
        r = (width - 1) // 2
        for px, py in points:
            if r <= 0:
                self.set_pixel(px, py, color)
            else:
                self._brush(px, py, r, color)

    def draw_circle(self, cx, cy, radius, color=None, fill_color=None, width=1):
        cx, cy, radius = int(cx), int(cy), int(radius)
        if fill_color is not None:
            for y in range(cy - radius, cy + radius + 1):
                for x in range(cx - radius, cx + radius + 1):
                    if (x - cx) ** 2 + (y - cy) ** 2 <= radius ** 2:
                        self.set_pixel(x, y, fill_color)
        x = 0
        y = radius
        d = 3 - 2 * radius
        r = (width - 1) // 2
        while x <= y:
            for sx, sy in [(x, y), (-x, y), (x, -y), (-x, -y),
                           (y, x), (-y, x), (y, -x), (-y, -x)]:
                if r <= 0:
                    self.set_pixel(cx + sx, cy + sy, color)
                else:
                    self._brush(cx + sx, cy + sy, r, color)
            if d < 0:
                d += 4 * x + 6
            else:
                d += 4 * (x - y) + 10
                y -= 1
            x += 1

    def draw_box(self, x, y, w, h, color=None, fill_color=None, width=1):
        x, y, w, h = int(x), int(y), int(w), int(h)
        if fill_color is not None:
            for py in range(y, y + h + 1):
                for px in range(x, x + w + 1):
                    self.set_pixel(px, py, fill_color)
        self.draw_line(x, y, x + w, y, color, width)
        self.draw_line(x + w, y, x + w, y + h, color, width)
        self.draw_line(x + w, y + h, x, y + h, color, width)
        self.draw_line(x, y + h, x, y, color, width)

    def draw_filled_box(self, x, y, w, h, color=None):
        x, y, w, h = int(x), int(y), int(w), int(h)
        for py in range(y, y + h + 1):
            for px in range(x, x + w + 1):
                self.set_pixel(px, py, color)

    def draw_text(self, x, y, size, text, color=None):
        col = x // 2
        row = y // 4
        self.texts.append((row, col, text))
        if color:
            for i in range(len(text)):
                c = col + i
                if 0 <= c < self.cols and 0 <= row < self.rows:
                    self.text_color[(row, c)] = color

    def render_lines(self):
        grid = []
        colors = []
        for row in range(self.rows):
            line = []
            color_line = []
            for col in range(self.cols):
                char_val = 0
                for dy in range(4):
                    for dx in range(2):
                        px = col * 2 + dx
                        py = row * 4 + dy
                        if (px, py) in self.pixels:
                            char_val |= DOTS[dy][dx]
                line.append(chr(BRAILLE_BASE + char_val))
                color_line.append(self.pixel_color.get((col, row)))
            grid.append(line)
            colors.append(color_line)

        for row, col, text in self.texts:
            if 0 <= row < self.rows:
                for i, ch in enumerate(text):
                    c = col + i
                    if 0 <= c < self.cols:
                        grid[row][c] = ch
                        tc = self.text_color.get((row, c))
                        if tc:
                            colors[row][c] = tc

        bg = ''
        if self.bg_color:
            bg = _ansi_bg(*self.bg_color)

        lines = []
        has_color = False
        for row in range(self.rows):
            parts = []
            prev_color = None
            for col in range(self.cols):
                cc = colors[row][col]
                if cc and cc != prev_color:
                    parts.append(_ansi_fg(*cc))
                    prev_color = cc
                    has_color = True
                elif not cc and prev_color:
                    parts.append('\033[39m')
                    prev_color = None
                parts.append(grid[row][col])
            if prev_color:
                parts.append('\033[39m')
            lines.append(bg + ''.join(parts))

        return lines, has_color or bool(bg)

    def render(self):
        lines, has_ansi = self.render_lines()
        reset = '\033[0m' if has_ansi else ''
        return '\n'.join(lines) + reset

    def display(self):
        out = sys.stdout
        out.write('\033[2J\033[H')
        out.flush()

        lines, has_ansi = self.render_lines()
        for line in lines:
            out.write(line)
            out.write('\n')
            out.flush()

        if has_ansi:
            out.write('\033[0m')
            out.flush()
