# FORTH CODE WORD: code/graphics/canvastext
# Draw text on the canvas

WORD_NAME = 'canvas-text'
#
# === CÓDIGO FORTH ORIGINAL ===
# ( x y size s -- ) Draw text string s at position (x,y) with font size
# Text is placed at approximate character position on braille canvas
# Uses current pen-color
# Example: 100 200 24 s" Hello" canvas-text
# === FIN CÓDIGO FORTH ===

def execute(forth):
    if len(forth.stack) < 4:
        print("Error: canvas-text requiere x y size texto")
        return
    text = forth.stack.pop()
    size = int(forth.stack.pop())
    y = int(forth.stack.pop())
    x = int(forth.stack.pop())

    if not isinstance(text, str):
        text = str(text)

    gfx = getattr(forth, '_gfx', None)
    if not gfx or not gfx.get('canvas'):
        print("Error: no hay canvas abierto (usa canvas-new)")
        return

    pen = gfx.get('pen_color', (255, 255, 255))
    gfx['canvas'].draw_text(x, y, size, text, pen)
