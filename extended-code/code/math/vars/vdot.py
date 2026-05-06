# FORTH CODE WORD: code/math/vars/vdot
# Print a vector

WORD_NAME = 'v.'
#
# === CÓDIGO FORTH ORIGINAL ===
# ( name|vec -- ) Print vector contents
# Usage: V1 v.   or   V1 v@ v.
# === FIN CÓDIGO FORTH ===

def execute(forth):
    if len(forth.stack) < 1:
        print("Error: v. requiere un vector en la pila")
        return

    v = forth.stack.pop()

    if isinstance(v, str):
        vecs = getattr(forth, 'vectors', {})
        if v in vecs:
            v = vecs[v]
        else:
            print(v)
            return

    if isinstance(v, list):
        parts = ' '.join(str(x) for x in v)
        print(f"[ {parts} ]")
    else:
        print(v)
