# FORTH CODE WORD: code/math/basics/mmul
# Matrix multiplication (numpy)

WORD_NAME = 'm*'
#
# === CÓDIGO FORTH ORIGINAL ===
# ( mat1 mat2 -- mat3 ) Matrix multiplication
# Usage: [| [| 1 2 |] [| 3 4 |] |] [| [| 2 0 |] [| 1 2 |] |] m* m.
# === FIN CÓDIGO FORTH ===

import numpy as np

def _resolve(forth, val):
    if isinstance(val, str):
        vecs = getattr(forth, 'vectors', {})
        if val in vecs:
            return vecs[val]
    return val

def execute(forth):
    if len(forth.stack) < 2:
        print("Error: m* requiere dos matrices")
        return

    b = _resolve(forth, forth.stack.pop())
    a = _resolve(forth, forth.stack.pop())

    try:
        result = np.matmul(a, b)
        forth.stack.append(result.tolist())
    except Exception as e:
        print(f"Error: m* - {e}")
        forth.stack.append(a)
        forth.stack.append(b)
