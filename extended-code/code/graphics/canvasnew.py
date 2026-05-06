# FORTH CODE WORD: code/graphics/canvasnew
# Create a new braille graphics canvas

WORD_NAME = 'canvas-new'
#
# === CÓDIGO FORTH ORIGINAL ===
# ( width height -- ) Create a braille canvas of given pixel size
# Resolution: 2x4 dots per character cell
# === FIN CÓDIGO FORTH ===

def execute(forth):
    if len(forth.stack) < 2:
        print("Error: canvas-new requiere width height")
        return
    h = int(forth.stack.pop())
    w = int(forth.stack.pop())

    if hasattr(forth, '_gfx') and forth._gfx.get('canvas'):
        forth._gfx['canvas'].clear()

    import os, sys
    sys.path.insert(0, os.path.dirname(__file__))
    from __braille_canvas import BrailleCanvas

    canvas = BrailleCanvas(w, h)

    forth._gfx = {
        'canvas': canvas,
        'pen_color': (255, 255, 255),
        'fill_color': None,
        'line_width': 1,
        'bg_color': None,
        'width': canvas.width,
        'height': canvas.height,
    }
