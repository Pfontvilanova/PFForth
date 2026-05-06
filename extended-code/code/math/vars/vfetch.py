# FORTH CODE WORD: code/math/vars/vfetch
# Read value from a named vector/matrix variable

WORD_NAME = 'v@'
#
# === CÓDIGO FORTH ORIGINAL ===
# ( name -- value ) Read value from named variable
# Usage: V1 v@ v.
# === FIN CÓDIGO FORTH ===

def execute(forth):
    if len(forth.stack) < 1:
        print("Error: v@ requiere nombre de variable")
        return

    name = forth.stack.pop()

    if not isinstance(name, str):
        print("Error: v@ requiere un nombre de variable")
        return

    vecs = getattr(forth, 'vectors', None)
    if vecs is None or name not in vecs:
        print(f"Error: variable '{name}' no existe")
        return

    forth.stack.append(forth.vectors[name])
