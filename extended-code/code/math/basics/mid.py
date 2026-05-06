# FORTH CODE WORD: code/math/basics/mid
# Identity matrix (numpy)

WORD_NAME = 'mid'
#
# === CÓDIGO FORTH ORIGINAL ===
# ( n -- mat ) Create n×n identity matrix
# Usage: 3 mid m.
# === FIN CÓDIGO FORTH ===

import numpy as np

def execute(forth):
    if len(forth.stack) < 1:
        print("Error: mid requiere un tamaño n")
        return

    n = forth.stack.pop()

    try:
        n = int(n)
        result = np.eye(n)
        forth.stack.append(result.astype(int).tolist())
    except Exception as e:
        print(f"Error: mid - {e}")
        forth.stack.append(n)
