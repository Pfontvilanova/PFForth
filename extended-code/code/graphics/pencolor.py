# FORTH CODE WORD: code/graphics/pencolor
# Set the pen (stroke) color for drawing

WORD_NAME = 'pen-color'
#
# === CÓDIGO FORTH ORIGINAL ===
# ( r g b -- ) Set pen color using RGB values 0-255
# === FIN CÓDIGO FORTH ===

def execute(forth):
    if len(forth.stack) < 3:
        print("Error: pen-color requiere r g b")
        return
    b = int(forth.stack.pop()) & 255
    g = int(forth.stack.pop()) & 255
    r = int(forth.stack.pop()) & 255
    if not hasattr(forth, '_gfx'):
        forth._gfx = {}
    forth._gfx['pen_color'] = (r, g, b)
