# FORTH CODE WORD: code/charts/charttitle
# Set chart title for next chart

WORD_NAME = 'chart-title'
#
# === CÓDIGO FORTH ORIGINAL ===
# ( str -- ) Set title for the next chart drawn
# Title is consumed (cleared) after chart is drawn
# === FIN CÓDIGO FORTH ===

def execute(forth):
    if len(forth.stack) < 1:
        print("Error: chart-title requiere un string")
        return
    title = forth.stack.pop()
    if not isinstance(title, str):
        title = str(title)
    if not hasattr(forth, '_chart_config'):
        forth._chart_config = {}
    forth._chart_config['title'] = title
