# FORTH CODE WORD: code/ai/vision/imgload
# Carga una imagen en el estado activo

WORD_NAME = 'img-load'
#
# === STACK EFFECT ===
# ( filename -- )  Carga imagen desde archivo, la deja como imagen activa
# === FIN ===


def _ensure_ai(forth):
    if not hasattr(forth, '_ai'):
        forth._ai = {}
    ai = forth._ai
    for k, v in {
        'dataset': None, 'target_col': None, 'train_set': None,
        'test_set': None, 'model': None, 'last_op': None,
        'verbose': False, 'image': None, 'image_path': None,
        'detections': None, 'audio': None, 'clip_model': None,
        'yolo_detect_model': None, 'yolo_classify_model': None,
        'ref_image': None, 'embedding': None, 'ref_embedding': None,
    }.items():
        ai.setdefault(k, v)


def execute(forth):
    import os
    _ensure_ai(forth)

    if not forth.stack:
        print("Error: img-load requiere nombre de archivo en la pila")
        return

    path = str(forth.stack.pop())

    try:
        from PIL import Image
    except ImportError:
        print("Error: Pillow no instalado — pip install Pillow")
        return

    try:
        img = Image.open(path)
        img.load()
        forth._ai['image']      = img
        forth._ai['image_path'] = path
        forth._ai['detections'] = None
        forth._ai['last_op'] = {
            'type':    'img-load',
            'data':    {'path': path, 'filename': os.path.basename(path)},
            'metrics': {'width': img.width, 'height': img.height, 'mode': img.mode},
        }
        print(f"✓ Imagen: {os.path.basename(path)}")
        print(f"  {img.width} × {img.height} px  |  modo: {img.mode}")
        if forth._ai.get('verbose'):
            print(f"  Canales: {len(img.getbands())}  |  Formato: {img.format or 'N/A'}")
    except FileNotFoundError:
        print(f"Error: archivo no encontrado — {path}")
    except Exception as e:
        print(f"Error img-load: {e}")
