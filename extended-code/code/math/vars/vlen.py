# FORTH CODE WORD: code/math/vars/vlen
# Get length of a vector

WORD_NAME = 'vlen'
#
# === CÓDIGO FORTH ORIGINAL ===
# ( name|vec -- n ) Get vector length
# Usage: v1 vlen .
# === FIN CÓDIGO FORTH ===

def execute(forth):
    if len(forth.stack) < 1:
        print("Error: vlen requiere un vector en la pila")
        return

    v = forth.stack.pop()

    if isinstance(v, str):
        vecs = getattr(forth, 'vectors', {})
        if v in vecs:
            v = vecs[v]
        else:
            print(f"Error: variable '{v}' no existe")
            return

    if isinstance(v, list):
        forth.stack.append(len(v))
    else:
        print("Error: vlen requiere un vector (lista)")
