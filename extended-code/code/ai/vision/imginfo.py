# FORTH CODE WORD: code/ai/vision/imginfo
# Muestra dimensiones, modo y canales de la imagen activa

WORD_NAME = 'img-info'
#
# === STACK EFFECT ===
# ( -- )  Muestra información completa de la imagen activa
# === FIN ===


def _ensure_ai(forth):
    if not hasattr(forth, '_ai'):
        forth._ai = {}
    ai = forth._ai
    for k, v in {
        'image': None, 'image_path': None, 'last_op': None, 'verbose': False,
    }.items():
        ai.setdefault(k, v)


def execute(forth):
    import os
    _ensure_ai(forth)

    img = forth._ai.get('image')
    if img is None:
        print("Error: no hay imagen activa — usa img-load primero")
        return

    path     = forth._ai.get('image_path', '')
    channels = len(img.getbands())
    filename = os.path.basename(path) if path else 'N/A'

    print(f"=== Imagen activa ===")
    print(f"  Archivo  : {filename}")
    print(f"  Tamaño   : {img.width} × {img.height} px")
    print(f"  Modo     : {img.mode}  ({channels} canal{'es' if channels > 1 else ''})")
    print(f"  Formato  : {img.format or 'N/A'}")

    try:
        size = os.path.getsize(path)
        print(f"  Fichero  : {size // 1024} KB")
    except Exception:
        pass

    forth._ai['last_op'] = {
        'type':    'img-info',
        'data':    {'path': path, 'filename': filename},
        'metrics': {'width': img.width, 'height': img.height,
                    'mode': img.mode, 'channels': channels},
    }
