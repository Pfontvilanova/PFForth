# FORTH CODE WORD: code/charts/sparkline
# Draw a sparkline (mini inline chart) from stack data

WORD_NAME = 'sparkline'
#
# === CÓDIGO FORTH ORIGINAL ===
# ( v1 v2 ... vn n -- ) Draw sparkline with n values from stack
# Single-line mini chart using Unicode block characters ▁▂▃▄▅▆▇█
# === FIN CÓDIGO FORTH ===

def execute(forth):
    if len(forth.stack) < 1:
        print("Error: sparkline requiere n (cantidad de valores)")
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

    blocks = '▁▂▃▄▅▆▇█'

    max_val = max(values)
    min_val = min(values)
    if max_val == min_val:
        max_val = min_val + 1
    val_range = max_val - min_val

    result = ""
    for v in values:
        idx = int((v - min_val) / val_range * 7)
        idx = max(0, min(7, idx))
        result += blocks[idx]

    print(f"  {result}  min:{min_val:g} max:{max_val:g}")
