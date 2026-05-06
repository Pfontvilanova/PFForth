# FORTH CODE WORD: code/math/mixed/vsadd
# Vector + scalar

WORD_NAME = 'vs+'
#
# === CÓDIGO FORTH ORIGINAL ===
# ( vec n -- vec' ) Add scalar to each element
# Usage: [| 1 2 3 |] 10 vs+ v.  → [ 11 12 13 ]
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
        print("Error: vs+ requiere vector y escalar")
        return

    n = forth.stack.pop()
    a = _resolve(forth, forth.stack.pop())

    try:
        result = np.add(a, n)
        forth.stack.append(result.tolist())
    except Exception as e:
        print(f"Error: vs+ - {e}")
