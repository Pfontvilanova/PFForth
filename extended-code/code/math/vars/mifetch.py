# FORTH CODE WORD: code/math/vars/mifetch
# Read element from matrix by row and column

WORD_NAME = 'mi@'
#
# === CÓDIGO FORTH ORIGINAL ===
# ( name|mat row col -- val ) Read element at (row, col) (0-based)
# Usage: M1 1 2 mi@   o   [| [| 1 2 3 |] [| 4 5 6 |] |] 1 2 mi@  → 6
# === FIN CÓDIGO FORTH ===

def execute(forth):
    if len(forth.stack) < 3:
        print("Error: mi@ requiere matriz, fila y columna")
        return

    col = forth.stack.pop()
    row = forth.stack.pop()
    m = forth.stack.pop()

    if isinstance(m, str):
        vecs = getattr(forth, 'vectors', {})
        if m in vecs:
            m = vecs[m]
        else:
            print(f"Error: variable '{m}' no existe")
            return

    if not isinstance(m, list) or not m or not isinstance(m[0], list):
        print("Error: mi@ requiere una matriz (lista de listas)")
        return

    try:
        row = int(row)
        col = int(col)
    except Exception:
        print("Error: mi@ requiere fila y columna enteras")
        return

    rows = len(m)
    cols = len(m[0])

    if row < 0 or row >= rows:
        print(f"Error: mi@ fila {row} fuera de rango (0..{rows-1})")
        return

    if col < 0 or col >= cols:
        print(f"Error: mi@ columna {col} fuera de rango (0..{cols-1})")
        return

    forth.stack.append(m[row][col])
