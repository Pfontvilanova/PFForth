# FORTH CODE WORD: code/math/basics/minv
# Matrix inverse (numpy)

WORD_NAME = 'minv'
#
# === CÓDIGO FORTH ORIGINAL ===
# ( mat -- mat' ) Inverse of a square matrix
# Usage: [| [| 1 2 |] [| 3 4 |] |] minv m.
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
        print("Error: minv requiere una matriz")
        return

    a = _resolve(forth, forth.stack.pop())

    try:
        result = np.linalg.inv(a)
        forth.stack.append(result.tolist())
    except np.linalg.LinAlgError:
        print("Error: minv - matriz singular (no invertible)")
        forth.stack.append(a)
    except Exception as e:
        print(f"Error: minv - {e}")
        forth.stack.append(a)
