# FORTH CODE WORD: code/math/vars/vifetch
# Read element from vector by index

WORD_NAME = 'vi@'
#
# === CÓDIGO FORTH ORIGINAL ===
# ( name|vec idx -- val ) Read element at index (0-based)
# Usage: V1 2 vi@   o   [| 10 20 30 |] 1 vi@  → 20
# === FIN CÓDIGO FORTH ===

def execute(forth):
    if len(forth.stack) < 2:
        print("Error: vi@ requiere vector e índice")
        return

    idx = forth.stack.pop()
    v = forth.stack.pop()

    if isinstance(v, str):
        vecs = getattr(forth, 'vectors', {})
        if v in vecs:
            v = vecs[v]
        else:
            print(f"Error: variable '{v}' no existe")
            return

    if not isinstance(v, list):
        print("Error: vi@ requiere un vector")
        return

    try:
        idx = int(idx)
    except Exception:
        print("Error: vi@ requiere un índice entero")
        return

    if idx < 0 or idx >= len(v):
        print(f"Error: vi@ índice {idx} fuera de rango (0..{len(v)-1})")
        return

    forth.stack.append(v[idx])
