# FORTH CODE WORD: code/math/basics/mrand
# Create random matrix and store in variable

WORD_NAME = 'mrand'
#
# === CÓDIGO FORTH ORIGINAL ===
# ( name rows cols -- ) Create random matrix with low values (0-9) and store
# Usage: s" M1" matrix:  M1 3 2 mrand
# === FIN CÓDIGO FORTH ===

import numpy as np

def execute(forth):
    if len(forth.stack) < 3:
        print("Error: mrand requiere nombre rows cols")
        print('Uso: M1 3 2 mrand')
        return

    cols = forth.stack.pop()
    rows = forth.stack.pop()
    name = forth.stack.pop()

    if not isinstance(name, str):
        print("Error: mrand requiere un nombre de variable")
        return

    vecs = getattr(forth, 'vectors', None)
    if vecs is None or name not in vecs:
        print(f"Error: variable '{name}' no existe (usa matrix: primero)")
        return

    try:
        rows = int(rows)
        cols = int(cols)
        mat = np.random.randint(0, 10, size=(rows, cols)).tolist()
        forth.vectors[name] = mat
    except Exception as e:
        print(f"Error: mrand - {e}")
