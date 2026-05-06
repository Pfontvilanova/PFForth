# FORTH CODE WORD: code/math/vars/mdot
# Print a matrix

WORD_NAME = 'm.'
#
# === CÓDIGO FORTH ORIGINAL ===
# ( name|mat -- ) Print matrix contents formatted
# Usage: M1 m.   or   M1 v@ m.
# === FIN CÓDIGO FORTH ===

def execute(forth):
    if len(forth.stack) < 1:
        print("Error: m. requiere una matriz en la pila")
        return

    m = forth.stack.pop()

    if isinstance(m, str):
        vecs = getattr(forth, 'vectors', {})
        if m in vecs:
            m = vecs[m]
        else:
            print(m)
            return

    if not isinstance(m, list) or not m:
        print(m)
        return

    if isinstance(m[0], list):
        col_widths = []
        for col in range(len(m[0])):
            w = max(len(str(row[col])) for row in m if col < len(row))
            col_widths.append(w)

        for i, row in enumerate(m):
            parts = ' '.join(str(x).rjust(col_widths[j]) for j, x in enumerate(row))
            if i == 0:
                print(f"[ [ {parts} ]")
            elif i == len(m) - 1:
                print(f"  [ {parts} ] ]")
            else:
                print(f"  [ {parts} ]")
    else:
        parts = ' '.join(str(x) for x in m)
        print(f"[ {parts} ]")
