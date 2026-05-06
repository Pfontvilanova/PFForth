# FORTH CODE WORD: code/ai/vision/detectcount
# Cuenta detecciones de un tipo específico

WORD_NAME = 'detect-count'
#
# === STACK EFFECT ===
# ( label -- n )  Cuenta cuántos objetos de ese tipo se detectaron
#                 Usa s" " (cadena vacía) para contar todos
# === FIN ===


def _ensure_ai(forth):
    if not hasattr(forth, '_ai'):
        forth._ai = {}
    forth._ai.setdefault('detections', None)


def execute(forth):
    _ensure_ai(forth)

    if not forth.stack:
        print("Error: detect-count requiere etiqueta en la pila  (ej: s\" person\" detect-count)")
        forth.stack.append(0)
        return

    label = str(forth.stack.pop()).strip().lower()

    detections = forth._ai.get('detections')
    if detections is None:
        print("Error: no hay detecciones — usa img-detect primero")
        forth.stack.append(0)
        return

    if label == '':
        count = len(detections)
    else:
        count = sum(1 for d in detections if d['label'].lower() == label)

    forth.stack.append(count)
