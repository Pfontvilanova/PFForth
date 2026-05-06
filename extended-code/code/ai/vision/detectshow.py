# FORTH CODE WORD: code/ai/vision/detectshow
# Muestra los resultados de la última detección

WORD_NAME = 'detect-show'
#
# === STACK EFFECT ===
# ( -- )  Muestra tabla de detecciones del último img-detect
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
        return

    if len(detections) == 0:
        print("  (ningún objeto detectado)")
        return

    print(f"  {'#':<4} {'Objeto':<22} {'Conf':>6}  {'Caja (x1,y1,x2,y2)':>24}")
    print(f"  {'─'*4} {'─'*22} {'─'*6}  {'─'*24}")
    for i, d in enumerate(detections, 1):
        box = d.get('box', [])
        box_str = f"({box[0]:.0f},{box[1]:.0f},{box[2]:.0f},{box[3]:.0f})" if len(box) == 4 else "N/A"
        print(f"  {i:<4} {d['label']:<22} {d['conf']:>6.3f}  {box_str:>24}")
    print(f"  Total: {len(detections)} objetos")
