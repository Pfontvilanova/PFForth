# FORTH CODE WORD: code/charts/xlabel
# Set X axis label for next chart

WORD_NAME = 'x-label'
#
# === CÓDIGO FORTH ORIGINAL ===
# ( str -- ) Set X axis label for the next chart drawn
# Label is consumed (cleared) after chart is drawn
# === FIN CÓDIGO FORTH ===

def execute(forth):
    if len(forth.stack) < 1:
        print("Error: x-label requiere un string")
        return
    label = forth.stack.pop()
    if not isinstance(label, str):
        label = str(label)
    if not hasattr(forth, '_chart_config'):
        forth._chart_config = {}
    forth._chart_config['x_label'] = label
