# FORTH CODE WORD: code/graphics/line
# Draw a line on the canvas

WORD_NAME = 'line'
#
# === CÓDIGO FORTH ORIGINAL ===
# ( x1 y1 x2 y2 -- ) Draw line from (x1,y1) to (x2,y2) in pixels
# Uses current pen-color and line-width
# === FIN CÓDIGO FORTH ===

def execute(forth):
    if len(forth.stack) < 4:
        print("Error: line requiere x1 y1 x2 y2")
        return
    y2 = int(forth.stack.pop())
    x2 = int(forth.stack.pop())
    y1 = int(forth.stack.pop())
    x1 = int(forth.stack.pop())

    gfx = getattr(forth, '_gfx', None)
    if not gfx or not gfx.get('canvas'):
        print("Error: no hay canvas abierto (usa canvas-new)")
        return

    pen = gfx.get('pen_color', (255, 255, 255))
    lw = gfx.get('line_width', 1)

    gfx['canvas'].draw_line(x1, y1, x2, y2, pen, lw)
