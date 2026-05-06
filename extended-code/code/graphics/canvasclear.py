# FORTH CODE WORD: code/graphics/canvasclear
# Clear all drawings from the canvas

WORD_NAME = 'canvas-clear'
#
# === CÓDIGO FORTH ORIGINAL ===
# ( -- ) Clear all drawings from the canvas
# === FIN CÓDIGO FORTH ===

def execute(forth):
    gfx = getattr(forth, '_gfx', None)
    if not gfx or not gfx.get('canvas'):
        print("Error: no hay canvas abierto (usa canvas-new)")
        return
    gfx['canvas'].clear()
