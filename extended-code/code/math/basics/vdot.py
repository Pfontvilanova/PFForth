# FORTH CODE WORD: code/math/basics/vdot
# Dot product (numpy)

WORD_NAME = 'vdot'
#
# === CÓDIGO FORTH ORIGINAL ===
# ( vec1 vec2 -- n ) Dot product of two vectors
# Usage: [| 1 2 3 |] [| 4 5 6 |] vdot .  → 32
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
        print("Error: vdot requiere dos vectores")
        return

    b = _resolve(forth, forth.stack.pop())
    a = _resolve(forth, forth.stack.pop())

    try:
        result = np.dot(a, b)
        r = result.item() if hasattr(result, 'item') else result
        forth.stack.append(r)
    except Exception as e:
        print(f"Error: vdot - {e}")
        forth.stack.append(a)
        forth.stack.append(b)
