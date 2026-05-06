# FORTH CODE WORD: code/charts/ylabel
# Set Y axis label for next chart

WORD_NAME = 'y-label'
#
# === CÓDIGO FORTH ORIGINAL ===
# ( str -- ) Set Y axis label for the next chart drawn
# Label is consumed (cleared) after chart is drawn
# === FIN CÓDIGO FORTH ===

def execute(forth):
    if len(forth.stack) < 1:
        print("Error: y-label requiere un string")
        return
    label = forth.stack.pop()
    if not isinstance(label, str):
        label = str(label)
    if not hasattr(forth, '_chart_config'):
        forth._chart_config = {}
    forth._chart_config['y_label'] = label
