# FORTH CODE WORD: code/math/advanced/solve
# Solve linear system Ax = b

WORD_NAME = 'solve'
#
# === CÓDIGO FORTH ORIGINAL ===
# ( A b -- x ) Solve linear system Ax = b
# Usage: [| [| 3 1 |] [| 1 2 |] |] [| 9 8 |] solve v.
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
        print("Error: solve requiere matriz A y vector b")
        return

    b = _resolve(forth, forth.stack.pop())
    a = _resolve(forth, forth.stack.pop())

    try:
        result = np.linalg.solve(a, b)
        forth.stack.append(result.tolist())
    except np.linalg.LinAlgError as e:
        print(f"Error: solve - {e}")
    except Exception as e:
        print(f"Error: solve - {e}")
