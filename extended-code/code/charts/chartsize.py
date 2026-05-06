# FORTH CODE WORD: code/charts/chartsize
# Set chart dimensions for next chart

WORD_NAME = 'chart-size'
#
# === CÓDIGO FORTH ORIGINAL ===
# ( width height -- ) Set size in characters for the next chart drawn
# Size is consumed (cleared) after chart is drawn
# === FIN CÓDIGO FORTH ===

def execute(forth):
    if len(forth.stack) < 2:
        print("Error: chart-size requiere width height")
        return
    h = forth.stack.pop()
    w = forth.stack.pop()
    if not isinstance(w, int) or not isinstance(h, int) or w < 10 or h < 5:
        print("Error: chart-size requiere enteros (min 10x5)")
        return
    if not hasattr(forth, '_chart_config'):
        forth._chart_config = {}
    forth._chart_config['size'] = (w, h)
