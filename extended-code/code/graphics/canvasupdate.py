# FORTH CODE WORD: code/graphics/canvasupdate
# Render and display the braille canvas

WORD_NAME = 'canvas-update'
#
# === CÓDIGO FORTH ORIGINAL ===
# ( -- ) Render the canvas to terminal using braille characters
# === FIN CÓDIGO FORTH ===

def execute(forth):
    gfx = getattr(forth, '_gfx', None)
    if not gfx or not gfx.get('canvas'):
        print("Error: no hay canvas abierto (usa canvas-new)")
        return
    gfx['canvas'].display()
