# FORTH CODE WORD: code/ai/vision/imgcrop
# Recorta la imagen activa

WORD_NAME = 'img-crop'
#
# === STACK EFFECT ===
# ( x y w h -- )  Recorta desde (x,y) con tamaño w×h píxeles
# === FIN ===


def _ensure_ai(forth):
    if not hasattr(forth, '_ai'):
        forth._ai = {}
    forth._ai.setdefault('image', None)
    forth._ai.setdefault('last_op', None)


def execute(forth):
    _ensure_ai(forth)

    img = forth._ai.get('image')
    if img is None:
        print("Error: no hay imagen activa — usa img-load primero")
        return

    if len(forth.stack) < 4:
        print("Error: img-crop requiere ( x y w h ) en la pila")
        return

    h  = int(forth.stack.pop())
    w  = int(forth.stack.pop())
    y  = int(forth.stack.pop())
    x  = int(forth.stack.pop())
    x2 = x + w
    y2 = y + h

    if x < 0 or y < 0 or x2 > img.width or y2 > img.height:
        print(f"Error: recorte ({x},{y})→({x2},{y2}) fuera de los límites ({img.width}×{img.height})")
        return

    try:
        cropped = img.crop((x, y, x2, y2))
        forth._ai['image'] = cropped
        forth._ai['last_op'] = {
            'type':    'img-crop',
            'data':    {'x': x, 'y': y, 'w': w, 'h': h},
            'metrics': {'width': w, 'height': h},
        }
        print(f"✓ Recortada: ({x},{y}) tamaño {w}×{h} px")
    except Exception as e:
        print(f"Error img-crop: {e}")
