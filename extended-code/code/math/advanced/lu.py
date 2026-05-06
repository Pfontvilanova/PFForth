# FORTH CODE WORD: code/math/advanced/lu
# LU Decomposition

WORD_NAME = 'lu'
#
# === CÓDIGO FORTH ORIGINAL ===
# ( mat -- L U ) LU Decomposition
# Usage: [| [| 4 3 |] [| 6 3 |] |] lu
# === FIN CÓDIGO FORTH ===

import numpy as np
from scipy import linalg as sla

def _resolve(forth, val):
    if isinstance(val, str):
        vecs = getattr(forth, 'vectors', {})
        if val in vecs:
            return vecs[val]
    return val

def execute(forth):
    if len(forth.stack) < 1:
        print("Error: lu requiere una matriz")
        return

    a = _resolve(forth, forth.stack.pop())

    try:
        P, L, U = sla.lu(a)
        PL = np.dot(P, L)
        forth.stack.append(PL.tolist())
        forth.stack.append(U.tolist())
    except Exception as e:
        print(f"Error: lu - {e}")
