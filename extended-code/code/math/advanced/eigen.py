# FORTH CODE WORD: code/math/advanced/eigen
# Eigenvalues and eigenvectors

WORD_NAME = 'eigen'
#
# === CÓDIGO FORTH ORIGINAL ===
# ( mat -- eigenvalues eigenvectors ) Compute eigenvalues and eigenvectors
# Usage: [| [| 2 1 |] [| 1 2 |] |] eigen v. m.
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
        print("Error: eigen requiere una matriz")
        return

    a = _resolve(forth, forth.stack.pop())

    try:
        eigenvalues, eigenvectors = np.linalg.eig(a)
        forth.stack.append(eigenvalues.tolist())
        forth.stack.append(eigenvectors.tolist())
    except Exception as e:
        print(f"Error: eigen - {e}")
