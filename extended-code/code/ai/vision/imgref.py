# FORTH CODE WORD: code/ai/vision/imgref
# Guarda la imagen activa como referencia para similitud/anomalía

WORD_NAME = 'img-ref!'
#
# === STACK EFFECT ===
# ( -- )  Guarda imagen activa como referencia (para img-sim e img-anomaly)
# === FIN ===


def _ensure_ai(forth):
    if not hasattr(forth, '_ai'):
        forth._ai = {}
    forth._ai.setdefault('image', None)
    forth._ai.setdefault('ref_image', None)
    forth._ai.setdefault('ref_histogram', None)
    forth._ai.setdefault('image_path', None)
    forth._ai.setdefault('last_op', None)


def _image_histogram(img):
    """Genera histograma normalizado (RGB o L) para comparación."""
    from PIL import Image
    rgb = img.convert('RGB')
    hist = rgb.histogram()
    total = sum(hist) or 1
    return [v / total for v in hist]


def execute(forth):
    import os
    _ensure_ai(forth)

    img = forth._ai.get('image')
    if img is None:
        print("Error: no hay imagen activa — usa img-load primero")
        return

    try:
        forth._ai['ref_image']     = img.copy()
        forth._ai['ref_histogram'] = _image_histogram(img)
        path = forth._ai.get('image_path', '')
        print(f"✓ Referencia guardada: {os.path.basename(path) if path else 'imagen actual'}")
        print(f"  Usa img-sim para comparar  |  img-anomaly para detectar diferencias")
        forth._ai['last_op'] = {
            'type':    'img-ref!',
            'data':    {'path': path},
            'metrics': {'width': img.width, 'height': img.height},
        }
    except Exception as e:
        print(f"Error img-ref!: {e}")
