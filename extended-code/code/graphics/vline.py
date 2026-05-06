# FORTH CODE WORD: code/graphics/vline
# Draw a vertical line on the canvas

WORD_NAME = 'vline'
#
# === CÓDIGO FORTH ORIGINAL ===
# ( x y len -- ) Draw vertical line from (x,y) going down, given length in pixels
# Uses current pen-color and line-width
# === FIN CÓDIGO FORTH ===

def execute(forth):
    if len(forth.stack) < 3:
        print("Error: vline requiere x y len")
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

    gfx['canvas'].draw_line(x, y, x, y + length, pen, lw)
