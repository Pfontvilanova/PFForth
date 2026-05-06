# FORTH CODE WORD: code/math/vars/vstore
# Store a value into a named vector/matrix variable

WORD_NAME = 'v!'
#
# === CÓDIGO FORTH ORIGINAL ===
# ( value name -- ) Store value into named variable
# Usage: [1 2 3] V1 v!
# === FIN CÓDIGO FORTH ===

def execute(forth):
    if len(forth.stack) < 2:
        print("Error: v! requiere valor y nombre")
        return

    name = forth.stack.pop()
    value = forth.stack.pop()

    if not isinstance(name, str):
        print("Error: v! requiere un nombre de variable")
        return

    vecs = getattr(forth, 'vectors', None)
    if vecs is None or name not in vecs:
        print(f"Error: variable '{name}' no existe (usa vector o matrix)")
        return

    forth.vectors[name] = value
