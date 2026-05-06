# FORTH CODE WORD: code/graphics/boxangle
# Set rotation angle for box drawing

WORD_NAME = 'box-angle'
#
# === CÓDIGO FORTH ORIGINAL ===
# ( degrees -- ) Set rotation angle for box/filled-box (0 = no rotation)
# Rotation is around the origin point (x,y) of the box
# === FIN CÓDIGO FORTH ===

def execute(forth):
    if len(forth.stack) < 1:
        print("Error: box-angle requiere ángulo en grados")
        return
    angle = forth.stack.pop()

    gfx = getattr(forth, '_gfx', None)
    if not gfx:
        forth._gfx = {'box_angle': float(angle)}
    else:
        gfx['box_angle'] = float(angle)
