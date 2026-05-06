# FORTH CODE WORD: code/ai/vision/imgsize
# Deja ancho y alto de la imagen activa en la pila

WORD_NAME = 'img-size'
#
# === STACK EFFECT ===
# ( -- w h )  Ancho y alto de la imagen activa en píxeles
# === FIN ===


def _ensure_ai(forth):
    if not hasattr(forth, '_ai'):
        forth._ai = {}
    forth._ai.setdefault('image', None)


def execute(forth):
    _ensure_ai(forth)

    img = forth._ai.get('image')
    if img is None:
        print("Error: no hay imagen activa — usa img-load primero")
        forth.stack.append(0)
        forth.stack.append(0)
        return

    forth.stack.append(img.width)
    forth.stack.append(img.height)
