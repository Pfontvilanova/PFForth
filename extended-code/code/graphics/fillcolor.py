# FORTH CODE WORD: code/graphics/fillcolor
# Set the fill color for shapes

WORD_NAME = 'fill-color'
#
# === CÓDIGO FORTH ORIGINAL ===
# ( r g b -- ) Set fill color using RGB values 0-255
# Use -1 -1 -1 to disable fill (transparent)
# === FIN CÓDIGO FORTH ===

def execute(forth):
    if len(forth.stack) < 3:
        print("Error: fill-color requiere r g b")
        return
    b = int(forth.stack.pop())
    g = int(forth.stack.pop())
    r = int(forth.stack.pop())
    if not hasattr(forth, '_gfx'):
        forth._gfx = {}
    if r < 0 or g < 0 or b < 0:
        forth._gfx['fill_color'] = None
    else:
        forth._gfx['fill_color'] = (r & 255, g & 255, b & 255)
