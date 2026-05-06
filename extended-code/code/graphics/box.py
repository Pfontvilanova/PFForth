# FORTH CODE WORD: code/graphics/box
# Draw a rectangle on the canvas

WORD_NAME = 'box'
#
# === CÓDIGO FORTH ORIGINAL ===
# ( x y w h -- ) Draw rectangle at (x,y) with width w and height h in pixels
# Uses current pen-color, fill-color, line-width and box-angle
# Rotation is around the origin point (x,y)
# === FIN CÓDIGO FORTH ===

import math

def _rotate(px, py, ox, oy, angle_deg):
    if angle_deg == 0:
        return px, py
    rad = math.radians(angle_deg)
    cs = math.cos(rad)
    sn = math.sin(rad)
    dx = px - ox
    dy = py - oy
    return ox + dx * cs - dy * sn, oy + dx * sn + dy * cs

def execute(forth):
    if len(forth.stack) < 4:
        print("Error: box requiere x y w h")
        return
    h = int(forth.stack.pop())
    w = int(forth.stack.pop())
    y = int(forth.stack.pop())
    x = int(forth.stack.pop())

    gfx = getattr(forth, '_gfx', None)
    if not gfx or not gfx.get('canvas'):
        print("Error: no hay canvas abierto (usa canvas-new)")
        return

    pen = gfx.get('pen_color', (255, 255, 255))
    fill = gfx.get('fill_color', None)
    lw = gfx.get('line_width', 1)
    angle = gfx.get('box_angle', 0)

    if angle == 0:
        gfx['canvas'].draw_box(x, y, w, h, pen, fill, lw)
    else:
        corners = [
            (x, y),
            (x + w, y),
            (x + w, y + h),
            (x, y + h),
        ]
        rotated = [_rotate(px, py, x, y, angle) for px, py in corners]

        canvas = gfx['canvas']
        if fill is not None:
            _fill_rotated_box(canvas, rotated, fill)

        for i in range(4):
            x1, y1 = rotated[i]
            x2, y2 = rotated[(i + 1) % 4]
            canvas.draw_line(x1, y1, x2, y2, pen, lw)

def _fill_rotated_box(canvas, corners, color):
    xs = [c[0] for c in corners]
    ys = [c[1] for c in corners]
    min_y = int(min(ys))
    max_y = int(max(ys))
    for scan_y in range(min_y, max_y + 1):
        intersections = []
        for i in range(4):
            x1, y1 = corners[i]
            x2, y2 = corners[(i + 1) % 4]
            if y1 == y2:
                continue
            if min(y1, y2) <= scan_y <= max(y1, y2):
                t = (scan_y - y1) / (y2 - y1)
                ix = x1 + t * (x2 - x1)
                intersections.append(ix)
        intersections.sort()
        for j in range(0, len(intersections) - 1, 2):
            for px in range(int(intersections[j]), int(intersections[j + 1]) + 1):
                canvas.set_pixel(px, scan_y, color)
