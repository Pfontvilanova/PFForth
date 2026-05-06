# FORTH CODE WORD: code/ai/vision/imgresize
# Redimensiona la imagen activa a w×h píxeles

WORD_NAME = 'img-resize'
#
# === STACK EFFECT ===
# ( w h -- )  Redimensiona la imagen activa a w×h píxeles
# === FIN ===


def _ensure_ai(forth):
    if not hasattr(forth, '_ai'):
        forth._ai = {}
    forth._ai.setdefault('image', None)
    forth._ai.setdefault('last_op', None)
    forth._ai.setdefault('verbose', False)


def execute(forth):
    _ensure_ai(forth)

    img = forth._ai.get('image')
    if img is None:
        print("Error: no hay imagen activa — usa img-load primero")
        return

    if len(forth.stack) < 2:
        print("Error: img-resize requiere ( w h ) en la pila")
        return

    h = int(forth.stack.pop())
    w = int(forth.stack.pop())

    if w <= 0 or h <= 0:
        print(f"Error: dimensiones inválidas ({w}×{h})")
        return

    try:
        from PIL import Image
        orig_w, orig_h = img.width, img.height
        resized = img.resize((w, h), Image.LANCZOS)
        forth._ai['image'] = resized
        forth._ai['last_op'] = {
            'type':    'img-resize',
            'data':    {'from': f"{orig_w}×{orig_h}", 'to': f"{w}×{h}"},
            'metrics': {'width': w, 'height': h},
        }
        print(f"✓ Redimensionada: {orig_w}×{orig_h}  →  {w}×{h} px")
    except Exception as e:
        print(f"Error img-resize: {e}")
