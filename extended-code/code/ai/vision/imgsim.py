# FORTH CODE WORD: code/ai/vision/imgsim
# Similitud entre imagen activa y referencia (0.0 = diferente, 1.0 = idéntica)

WORD_NAME = 'img-sim'
#
# === STACK EFFECT ===
# ( -- score )  Similitud imagen activa vs referencia  (0.0 – 1.0)
#               Requiere img-ref! previo
# === FIN ===


def _ensure_ai(forth):
    if not hasattr(forth, '_ai'):
        forth._ai = {}
    forth._ai.setdefault('image', None)
    forth._ai.setdefault('ref_histogram', None)
    forth._ai.setdefault('last_op', None)


def _histogram(img):
    rgb  = img.convert('RGB')
    hist = rgb.histogram()
    total = sum(hist) or 1
    return [v / total for v in hist]


def _correlation(h1, h2):
    """Correlación de Pearson entre dos histogramas (resultado -1 a 1)."""
    n    = len(h1)
    m1   = sum(h1) / n
    m2   = sum(h2) / n
    num  = sum((a - m1) * (b - m2) for a, b in zip(h1, h2))
    den1 = sum((a - m1) ** 2 for a in h1) ** 0.5
    den2 = sum((b - m2) ** 2 for b in h2) ** 0.5
    denom = den1 * den2
    if denom == 0:
        return 1.0 if h1 == h2 else 0.0
    return max(0.0, min(1.0, num / denom))


def execute(forth):
    _ensure_ai(forth)

    img     = forth._ai.get('image')
    ref_h   = forth._ai.get('ref_histogram')

    if img is None:
        print("Error: no hay imagen activa — usa img-load primero")
        forth.stack.append(0.0)
        return

    if ref_h is None:
        print("Error: no hay referencia — usa img-ref! primero")
        forth.stack.append(0.0)
        return

    try:
        cur_h = _histogram(img)
        score = round(_correlation(ref_h, cur_h), 4)

        if score >= 0.95:
            nivel = "muy similar"
        elif score >= 0.80:
            nivel = "similar"
        elif score >= 0.60:
            nivel = "algo diferente"
        else:
            nivel = "muy diferente"

        print(f"✓ Similitud: {score:.4f}  ({nivel})")

        forth._ai['last_op'] = {
            'type':    'img-sim',
            'data':    {},
            'metrics': {'score': score},
        }
        forth.stack.append(score)

    except Exception as e:
        print(f"Error img-sim: {e}")
        forth.stack.append(0.0)
