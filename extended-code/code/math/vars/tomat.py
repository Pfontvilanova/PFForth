# FORTH CODE WORD: code/math/vars/tomat
# Build a matrix from stack values

WORD_NAME = '>mat'
#
# === CÓDIGO FORTH ORIGINAL ===
# ( v1 ... cols rows -- mat ) Build matrix from stack values
# Usage: 1 2 3 4 2 2 >mat
# Result: [[1, 2], [3, 4]]
# === FIN CÓDIGO FORTH ===

def execute(forth):
    if len(forth.stack) < 2:
        print("Error: >mat requiere cols rows")
        return

    rows = forth.stack.pop()
    cols = forth.stack.pop()

    if not isinstance(rows, int) or not isinstance(cols, int):
        print("Error: >mat requiere enteros para cols y rows")
        return

    total = rows * cols
    if len(forth.stack) < total:
        print(f"Error: >mat necesita {total} valores en la pila ({cols}x{rows})")
        forth.stack.extend([cols, rows])
        return

    values = []
    for _ in range(total):
        values.insert(0, forth.stack.pop())

    mat = []
    for r in range(rows):
        row = values[r * cols : (r + 1) * cols]
        mat.append(row)

    forth.stack.append(mat)
