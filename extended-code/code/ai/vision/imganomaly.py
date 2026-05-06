# FORTH CODE WORD: code/ai/vision/imganomaly
# Detecta anomalías comparando imagen activa con la referencia

WORD_NAME = 'img-anomaly'
#
# === STACK EFFECT ===
# ( threshold -- flag )  Compara imagen activa vs referencia.
#                        flag=-1 si anomalía detectada, 0 si normal.
#                        Usa img-ref! para fijar la referencia normal.
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

    if not forth.stack:
        print("Error: img-anomaly requiere ( threshold ) en la pila")
        forth.stack.append(0)
        return

    threshold = float(forth.stack.pop())

    img   = forth._ai.get('image')
    ref_h = forth._ai.get('ref_histogram')

    if img is None:
        print("Error: no hay imagen activa — usa img-load primero")
        forth.stack.append(0)
        return

    if ref_h is None:
        print("Error: no hay referencia — usa img-ref! primero")
        forth.stack.append(0)
        return

    try:
        cur_h   = _histogram(img)
        sim     = round(_correlation(ref_h, cur_h), 4)
        anomaly = sim < threshold
        flag    = -1 if anomaly else 0

        estado = "⚠ ANOMALÍA" if anomaly else "✓ Normal"
        print(f"{estado}  |  similitud: {sim:.4f}  (umbral: {threshold})")

        forth._ai['last_op'] = {
            'type':    'img-anomaly',
            'data':    {'threshold': threshold},
            'metrics': {'similarity': sim, 'anomaly': anomaly},
        }
        forth.stack.append(flag)

    except Exception as e:
        print(f"Error img-anomaly: {e}")
        forth.stack.append(0)
