# FORTH CODE WORD: code/math/vars/vlist
# List all vector and matrix variables

WORD_NAME = 'mlist'
#
# === CÓDIGO FORTH ORIGINAL ===
# ( -- ) List all created vector/matrix variables
# Usage: mlist
# === FIN CÓDIGO FORTH ===

def execute(forth):
    vecs = getattr(forth, 'vectors', {})

    if not vecs:
        print("No hay vectores ni matrices definidos")
        return

    for name, val in vecs.items():
        if val is None:
            print(f"  {name:12s} (vacío)")
        elif isinstance(val, list) and val and isinstance(val[0], list):
            rows = len(val)
            cols = len(val[0])
            print(f"  {name:12s} matriz {rows}x{cols}")
        elif isinstance(val, list):
            print(f"  {name:12s} vector [{len(val)}]")
        else:
            print(f"  {name:12s} = {val}")
