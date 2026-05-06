# FORTH CODE WORD: code/graphics/filledbox
# Draw a filled rectangle on the canvas

WORD_NAME = 'filled-box'
#
# === CÓDIGO FORTH ORIGINAL ===
# ( x y w h -- ) Draw filled rectangle at (x,y) with width w and height h
# Uses current pen-color as fill, respects box-angle
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
        print("Error: filled-box requiere x y w h")
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
    angle = gfx.get('box_angle', 0)

    if angle == 0:
        gfx['canvas'].draw_filled_box(x, y, w, h, pen)
    else:
        corners = [
            (x, y),
            (x + w, y),
            (x + w, y + h),
            (x, y + h),
        ]
        rotated = [_rotate(px, py, x, y, angle) for px, py in corners]

        canvas = gfx['canvas']
        xs = [c[0] for c in rotated]
        ys = [c[1] for c in rotated]
        min_y = int(min(ys))
        max_y = int(max(ys))
        for scan_y in range(min_y, max_y + 1):
            intersections = []
            for i in range(4):
                x1, y1 = rotated[i]
                x2, y2 = rotated[(i + 1) % 4]
                if y1 == y2:
                    continue
                if min(y1, y2) <= scan_y <= max(y1, y2):
                    t = (scan_y - y1) / (y2 - y1)
                    ix = x1 + t * (x2 - x1)
                    intersections.append(ix)
            intersections.sort()
            for j in range(0, len(intersections) - 1, 2):
                for px in range(int(intersections[j]), int(intersections[j + 1]) + 1):
                    canvas.set_pixel(px, scan_y, pen)
