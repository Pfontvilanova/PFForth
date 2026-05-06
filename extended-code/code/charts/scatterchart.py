# FORTH CODE WORD: code/charts/scatterchart
# Draw a scatter plot using plotext

WORD_NAME = 'scatter-chart'
#
# === CÓDIGO FORTH ORIGINAL ===
# ( x1 y1 x2 y2 ... xn yn n -- ) Draw scatter plot with n x,y pairs
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
        print("Error: scatter-chart requiere n (cantidad de puntos)")
        return
    n = forth.stack.pop()
    if not isinstance(n, int) or n < 1:
        print("Error: n debe ser entero positivo")
        return
    if len(forth.stack) < n * 2:
        print(f"Error: se necesitan {n * 2} valores (x y pares) en la pila")
        forth.stack.append(n)
        return

    pairs = []
    for _ in range(n):
        y = forth.stack.pop()
        x = forth.stack.pop()
        pairs.insert(0, (x, y))

    title, x_lab, y_lab, size = _get_config(forth)
    xs = [p[0] for p in pairs]
    ys = [p[1] for p in pairs]

    plt.clear_figure()
    if size:
        plt.plotsize(size[0], size[1])
    plt.scatter(xs, ys, marker='dot')
    if title:
        plt.title(title)
    if x_lab:
        plt.xlabel(x_lab)
    if y_lab:
        plt.ylabel(y_lab)
    plt.show()
