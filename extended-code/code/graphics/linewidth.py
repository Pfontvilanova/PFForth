# FORTH CODE WORD: code/graphics/linewidth
# Set the line width for drawing

WORD_NAME = 'line-width'
#
# === CÓDIGO FORTH ORIGINAL ===
# ( n -- ) Set line width in pixels
# === FIN CÓDIGO FORTH ===

def execute(forth):
    if len(forth.stack) < 1:
        print("Error: line-width requiere n")
        return
    w = int(forth.stack.pop())
    if w < 1:
        w = 1
    if not hasattr(forth, '_gfx'):
        forth._gfx = {}
    forth._gfx['line_width'] = w
