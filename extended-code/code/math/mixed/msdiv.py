# FORTH CODE WORD: code/math/mixed/msdiv
# Matrix / scalar

WORD_NAME = 'ms/'
#
# === CÓDIGO FORTH ORIGINAL ===
# ( mat n -- mat' ) Divide each element by scalar
# Usage: A 2 ms/ m.
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
        print("Error: ms/ requiere matriz y escalar")
        return

    n = forth.stack.pop()
    a = _resolve(forth, forth.stack.pop())

    if n == 0:
        print("Error: ms/ división por cero")
        return

    try:
        result = np.divide(a, n)
        forth.stack.append(result.tolist())
    except Exception as e:
        print(f"Error: ms/ - {e}")
