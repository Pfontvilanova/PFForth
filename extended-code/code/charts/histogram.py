# FORTH CODE WORD: code/charts/histogram
# Draw a histogram using plotext

WORD_NAME = 'histogram'
#
# === CÓDIGO FORTH ORIGINAL ===
# ( v1 v2 ... vn n bins -- ) Draw histogram with n values grouped into bins
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
    if len(forth.stack) < 2:
        print("Error: histogram requiere valores... n bins")
        print("  Ejemplo: 1 2 3 4 5  5 10 histogram")
        print("           ^valores^  n bins")
        return
    bins = forth.stack.pop()
    n = forth.stack.pop()
    if not isinstance(n, int) or n < 1:
        print(f"Error: n={n} debe ser entero positivo")
        print("  Uso: valores... n bins histogram")
        return
    if not isinstance(bins, int) or bins < 1:
        print(f"Error: bins={bins} debe ser entero positivo")
        print("  Uso: valores... n bins histogram")
        return
    if len(forth.stack) < n:
        print(f"Error: se necesitan {n} valores pero solo hay {len(forth.stack)} en la pila")
        print(f"  Recuerda: valores... n bins histogram")
        print(f"  Ejemplo: 1 2 3 4 5  5 10 histogram  ( 5 valores, 10 bins )")
        forth.stack.append(n)
        forth.stack.append(bins)
        return

    values = []
    for _ in range(n):
        values.insert(0, forth.stack.pop())

    title, x_lab, y_lab, size = _get_config(forth)

    plt.clear_figure()
    if size:
        plt.plotsize(size[0], size[1])
    plt.hist(values, bins=bins)
    if title:
        plt.title(title)
    if x_lab:
        plt.xlabel(x_lab)
    if y_lab:
        plt.ylabel(y_lab)
    plt.show()
