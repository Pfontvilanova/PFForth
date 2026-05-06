# FORTH CODE WORD: code/graphics/hline
# Draw a horizontal line on the canvas

WORD_NAME = 'hline'
#
# === CÓDIGO FORTH ORIGINAL ===
# ( x y len -- ) Draw horizontal line from (x,y) with given length in pixels
# Uses current pen-color and line-width
# === FIN CÓDIGO FORTH ===

def execute(forth):
    if len(forth.stack) < 3:
        print("Error: hline requiere x y len")
        return
    length = int(forth.stack.pop())
    y = int(forth.stack.pop())
    x = int(forth.stack.pop())

    gfx = getattr(forth, '_gfx', None)
    if not gfx or not gfx.get('canvas'):
        print("Error: no hay canvas abierto (usa canvas-new)")
        return

    pen = gfx.get('pen_color', (255, 255, 255))
    lw = gfx.get('line_width', 1)

    gfx['canvas'].draw_line(x, y, x + length, y, pen, lw)
