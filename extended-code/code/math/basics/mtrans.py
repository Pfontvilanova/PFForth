# FORTH CODE WORD: code/math/basics/mtrans
# Matrix transpose (numpy)

WORD_NAME = 'mtrans'
#
# === CÓDIGO FORTH ORIGINAL ===
# ( mat -- mat' ) Transpose matrix
# Usage: [| [| 1 2 3 |] [| 4 5 6 |] |] mtrans m.
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
        print("Error: mtrans requiere una matriz")
        return

    a = _resolve(forth, forth.stack.pop())

    try:
        result = np.transpose(a)
        forth.stack.append(result.tolist())
    except Exception as e:
        print(f"Error: mtrans - {e}")
        forth.stack.append(a)
