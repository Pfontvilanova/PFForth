# FORTH CODE WORD: code/math/mixed/vsdiv
# Vector / scalar

WORD_NAME = 'vs/'
#
# === CÓDIGO FORTH ORIGINAL ===
# ( vec n -- vec' ) Divide each element by scalar
# Usage: [| 10 20 30 |] 5 vs/ v.  → [ 2.0 4.0 6.0 ]
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
        print("Error: vs/ requiere vector y escalar")
        return

    n = forth.stack.pop()
    a = _resolve(forth, forth.stack.pop())

    if n == 0:
        print("Error: vs/ división por cero")
        return

    try:
        result = np.divide(a, n)
        forth.stack.append(result.tolist())
    except Exception as e:
        print(f"Error: vs/ - {e}")
