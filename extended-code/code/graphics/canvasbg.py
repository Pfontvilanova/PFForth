# FORTH CODE WORD: code/graphics/canvasbg
# Set canvas background color

WORD_NAME = 'canvas-bg'
#
# === CÓDIGO FORTH ORIGINAL ===
# ( r g b -- ) Set canvas background color using RGB values 0-255
# === FIN CÓDIGO FORTH ===

def execute(forth):
    if len(forth.stack) < 3:
        print("Error: canvas-bg requiere r g b")
        return
    b = int(forth.stack.pop()) & 255
    g = int(forth.stack.pop()) & 255
    r = int(forth.stack.pop()) & 255
    gfx = getattr(forth, '_gfx', None)
    if not gfx:
        forth._gfx = {}
        gfx = forth._gfx
    gfx['bg_color'] = (r, g, b)
    if gfx.get('canvas'):
        gfx['canvas'].bg_color = (r, g, b)
