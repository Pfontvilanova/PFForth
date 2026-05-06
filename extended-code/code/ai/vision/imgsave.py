# FORTH CODE WORD: code/ai/vision/imgsave
# Guarda la imagen activa en disco

WORD_NAME = 'img-save'
#
# === STACK EFFECT ===
# ( filename -- )  Guarda la imagen activa en disco
# === FIN ===


def _ensure_ai(forth):
    if not hasattr(forth, '_ai'):
        forth._ai = {}
    forth._ai.setdefault('image', None)
    forth._ai.setdefault('image_path', None)
    forth._ai.setdefault('last_op', None)


def execute(forth):
    import os
    _ensure_ai(forth)

    img = forth._ai.get('image')
    if img is None:
        print("Error: no hay imagen activa — usa img-load primero")
        return

    if not forth.stack:
        print("Error: img-save requiere nombre de archivo en la pila")
        return

    path = str(forth.stack.pop())

    try:
        img.save(path)
        size = os.path.getsize(path)
        forth._ai['last_op'] = {
            'type':    'img-save',
            'data':    {'path': path},
            'metrics': {'width': img.width, 'height': img.height, 'size_kb': size // 1024},
        }
        print(f"✓ Guardada: {os.path.basename(path)}  ({size // 1024} KB)")
    except Exception as e:
        print(f"Error img-save: {e}")
