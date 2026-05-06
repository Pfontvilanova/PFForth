# FORTH CODE WORD: code/graphics/circle
# Draw a circle on the canvas

WORD_NAME = 'circle'
#
# === CÓDIGO FORTH ORIGINAL ===
# ( cx cy r -- ) Draw circle centered at cx,cy with radius r in pixels
# Uses current pen-color, fill-color and line-width
# === FIN CÓDIGO FORTH ===

def execute(forth):
    if len(forth.stack) < 3:
        print("Error: circle requiere cx cy r")
        return
    r = int(forth.stack.pop())
    cy = int(forth.stack.pop())
    cx = int(forth.stack.pop())

    gfx = getattr(forth, '_gfx', None)
    if not gfx or not gfx.get('canvas'):
        print("Error: no hay canvas abierto (usa canvas-new)")
        return

    pen = gfx.get('pen_color', (255, 255, 255))
    fill = gfx.get('fill_color', None)
    lw = gfx.get('line_width', 1)

    gfx['canvas'].draw_circle(cx, cy, r, pen, fill, lw)
