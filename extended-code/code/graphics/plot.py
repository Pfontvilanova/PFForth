# FORTH CODE WORD: code/graphics/plot
# Draw a point on the canvas

WORD_NAME = 'plot'
#
# === CÓDIGO FORTH ORIGINAL ===
# ( x y -- ) Draw a point at position (x,y) in pixels
# Size depends on current line-width, color from pen-color
# === FIN CÓDIGO FORTH ===

def execute(forth):
    if len(forth.stack) < 2:
        print("Error: plot requiere x y")
        return
    y = int(forth.stack.pop())
    x = int(forth.stack.pop())

    gfx = getattr(forth, '_gfx', None)
    if not gfx or not gfx.get('canvas'):
        print("Error: no hay canvas abierto (usa canvas-new)")
        return

    pen = gfx.get('pen_color', (255, 255, 255))
    lw = gfx.get('line_width', 1)
    canvas = gfx['canvas']
    r = (lw - 1) // 2

    if r <= 0:
        canvas.set_pixel(x, y, pen)
    else:
        canvas._brush(x, y, r, pen)
