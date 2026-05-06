# FORTH CODE WORD: code/math/advanced/svd
# Singular Value Decomposition

WORD_NAME = 'svd'
#
# === CÓDIGO FORTH ORIGINAL ===
# ( mat -- U S Vt ) Singular Value Decomposition
# Usage: [| [| 1 2 |] [| 3 4 |] |] svd
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
        print("Error: svd requiere una matriz")
        return

    a = _resolve(forth, forth.stack.pop())

    try:
        U, S, Vt = np.linalg.svd(a)
        forth.stack.append(U.tolist())
        forth.stack.append(S.tolist())
        forth.stack.append(Vt.tolist())
    except Exception as e:
        print(f"Error: svd - {e}")
