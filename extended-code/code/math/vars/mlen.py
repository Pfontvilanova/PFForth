# FORTH CODE WORD: code/math/vars/mlen
# Get dimensions of a matrix

WORD_NAME = 'mlen'
#
# === CÓDIGO FORTH ORIGINAL ===
# ( name|mat -- rows cols ) Get matrix dimensions
# Usage: M1 mlen . .   \ prints cols then rows
# === FIN CÓDIGO FORTH ===

def execute(forth):
    if len(forth.stack) < 1:
        print("Error: mlen requiere una matriz en la pila")
        return

    m = forth.stack.pop()

    if isinstance(m, str):
        vecs = getattr(forth, 'vectors', {})
        if m in vecs:
            m = vecs[m]
        else:
            print(f"Error: variable '{m}' no existe")
            return

    if not isinstance(m, list) or not m:
        print("Error: mlen requiere una matriz (lista de listas)")
        return

    if isinstance(m[0], list):
        rows = len(m)
        cols = len(m[0])
        forth.stack.append(rows)
        forth.stack.append(cols)
    else:
        forth.stack.append(len(m))
        forth.stack.append(1)
