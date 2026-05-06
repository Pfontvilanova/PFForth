# FORTH CODE WORD: code/charts/hbarchart
# Draw a horizontal bar chart using plotext

WORD_NAME = 'hbar-chart'
#
# === CÓDIGO FORTH ORIGINAL ===
# ( v1 v2 ... vn n -- ) Draw horizontal bar chart with n values from stack
# Use chart-title, x-label, y-label, chart-size before calling.
# === FIN CÓDIGO FORTH ===

import plotext as plt

def _get_config(forth):
    cfg = getattr(forth, '_chart_config', {})
    title = cfg.pop('title', None)
    x_lab = cfg.pop('x_label', None)
    y_lab = cfg.pop('y_label', None)
    size = cfg.pop('size', None)
    return title, x_lab, y_lab, size

def execute(forth):
    if len(forth.stack) < 1:
        print("Error: hbar-chart requiere n (cantidad de valores)")
        return
    n = forth.stack.pop()
    if not isinstance(n, int) or n < 1:
        print("Error: n debe ser entero positivo")
        return
    if len(forth.stack) < n:
        print(f"Error: se necesitan {n} valores en la pila")
        forth.stack.append(n)
        return

    values = []
    for _ in range(n):
        values.insert(0, forth.stack.pop())

    title, x_lab, y_lab, size = _get_config(forth)
    labels = [str(i + 1) for i in range(n)]

    plt.clear_figure()
    if size:
        plt.plotsize(size[0], size[1])
    plt.bar(labels, values, orientation='horizontal')
    if title:
        plt.title(title)
    if x_lab:
        plt.xlabel(x_lab)
    if y_lab:
        plt.ylabel(y_lab)
    plt.show()
