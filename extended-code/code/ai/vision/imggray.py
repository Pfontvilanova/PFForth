# FORTH CODE WORD: code/ai/vision/imggray
# Convierte la imagen activa a escala de grises

WORD_NAME = 'img-gray'
#
# === STACK EFFECT ===
# ( -- )  Convierte la imagen activa a escala de grises (modo L)
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

    try:
        prev_mode = img.mode
        gray = img.convert('L')
        forth._ai['image'] = gray
        forth._ai['last_op'] = {
            'type':    'img-gray',
            'data':    {'from_mode': prev_mode, 'to_mode': 'L'},
            'metrics': {'width': gray.width, 'height': gray.height},
        }
        print(f"✓ Convertida a grises ({prev_mode} → L)  |  {gray.width}×{gray.height} px")
    except Exception as e:
        print(f"Error img-gray: {e}")
