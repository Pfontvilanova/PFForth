# FORTH CODE WORD: code/math/basics/vplus
# Vector addition (numpy)

WORD_NAME = 'v+'
#
# === CÓDIGO FORTH ORIGINAL ===
# ( vec1 vec2 -- vec3 ) Element-wise vector addition
# Usage: [| 1 2 3 |] [| 4 5 6 |] v+ v.  → [ 5 7 9 ]
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
        print("Error: v+ requiere dos vectores")
        return

    b = _resolve(forth, forth.stack.pop())
    a = _resolve(forth, forth.stack.pop())

    try:
        result = np.add(a, b)
        forth.stack.append(result.tolist())
    except Exception as e:
        print(f"Error: v+ - {e}")
        forth.stack.append(a)
        forth.stack.append(b)
