# FORTH CODE WORD: code/math/basics/vcross
# Cross product (numpy)

WORD_NAME = 'vcross'
#
# === CÓDIGO FORTH ORIGINAL ===
# ( vec1 vec2 -- vec3 ) Cross product of two 3D vectors
# Usage: [| 1 0 0 |] [| 0 1 0 |] vcross v.  → [ 0 0 1 ]
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
        print("Error: vcross requiere dos vectores")
        return

    b = _resolve(forth, forth.stack.pop())
    a = _resolve(forth, forth.stack.pop())

    try:
        result = np.cross(a, b)
        forth.stack.append(result.tolist())
    except Exception as e:
        print(f"Error: vcross - {e}")
        forth.stack.append(a)
        forth.stack.append(b)
