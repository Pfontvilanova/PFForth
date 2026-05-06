# FORTH CODE WORD: code/math/basics/vminus
# Vector subtraction (numpy)

WORD_NAME = 'v-'
#
# === CÓDIGO FORTH ORIGINAL ===
# ( vec1 vec2 -- vec3 ) Element-wise vector subtraction
# Usage: [| 4 5 6 |] [| 1 1 1 |] v- v.  → [ 3 4 5 ]
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
        print("Error: v- requiere dos vectores")
        return

    b = _resolve(forth, forth.stack.pop())
    a = _resolve(forth, forth.stack.pop())

    try:
        result = np.subtract(a, b)
        forth.stack.append(result.tolist())
    except Exception as e:
        print(f"Error: v- - {e}")
        forth.stack.append(a)
        forth.stack.append(b)
