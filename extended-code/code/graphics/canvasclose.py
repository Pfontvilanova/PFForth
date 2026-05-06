# FORTH CODE WORD: code/graphics/canvasclose
# Close the canvas

WORD_NAME = 'canvas-close'
#
# === CÓDIGO FORTH ORIGINAL ===
# ( -- ) Close the graphics canvas
# === FIN CÓDIGO FORTH ===

def execute(forth):
    gfx = getattr(forth, '_gfx', None)
    if not gfx or not gfx.get('canvas'):
        return
    import sys
    sys.stdout.write('\033[0m\033[2J\033[H')
    sys.stdout.flush()
    forth._gfx = {}
