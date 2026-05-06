# FORTH CODE WORD: code/math/basics/mdet
# Matrix determinant (numpy)

WORD_NAME = 'mdet'
#
# === CÓDIGO FORTH ORIGINAL ===
# ( mat -- n ) Determinant of a square matrix
# Usage: [| [| 1 2 |] [| 3 4 |] |] mdet .  → -2.0
# === FIN CÓDIGO FORTH ===

import numpy as np

def _resolve(forth, val):
    if isinstance(val, str):
        vecs = getattr(forth, 'vectors', {})
        if val in vecs:
            return vecs[val]
    return val

def execute(forth):
    if len(forth.stack) < 1:
        print("Error: mdet requiere una matriz")
        return

    a = _resolve(forth, forth.stack.pop())

    try:
        result = np.linalg.det(a)
        forth.stack.append(float(result))
    except Exception as e:
        print(f"Error: mdet - {e}")
        forth.stack.append(a)
