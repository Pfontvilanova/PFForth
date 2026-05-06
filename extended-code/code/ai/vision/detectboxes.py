# FORTH CODE WORD: code/ai/vision/detectboxes
# Deja la lista de cajas detectadas en la pila

WORD_NAME = 'detect-boxes'
#
# === STACK EFFECT ===
# ( -- list )  Deja lista de dicts {label, conf, box} en la pila
#              Cada box = [x1, y1, x2, y2] en píxeles
# === FIN ===


def _ensure_ai(forth):
    if not hasattr(forth, '_ai'):
        forth._ai = {}
    forth._ai.setdefault('detections', None)


def execute(forth):
    _ensure_ai(forth)

    detections = forth._ai.get('detections')
    if detections is None:
        print("Error: no hay detecciones — usa img-detect primero")
        forth.stack.append([])
        return

    forth.stack.append(list(detections))
