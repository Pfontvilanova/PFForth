# FORTH CODE WORD: code/math/advanced/qr
# QR Decomposition

WORD_NAME = 'qr'
#
# === CÓDIGO FORTH ORIGINAL ===
# ( mat -- Q R ) QR Decomposition
# Usage: [| [| 1 2 |] [| 3 4 |] |] qr
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
        print("Error: qr requiere una matriz")
        return

    a = _resolve(forth, forth.stack.pop())

    try:
        Q, R = np.linalg.qr(a)
        forth.stack.append(Q.tolist())
        forth.stack.append(R.tolist())
    except Exception as e:
        print(f"Error: qr - {e}")
