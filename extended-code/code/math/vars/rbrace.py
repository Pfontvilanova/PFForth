# FORTH CODE WORD: code/math/vars/rbrace
# End list literal - collects values since marker into a list

WORD_NAME = '|]'
#
# === CÓDIGO FORTH ORIGINAL ===
# ( marker v1 v2 ... vn -- list ) Collect values into list
# Usage: [| 1 2 3 |] v1 v!
# === FIN CÓDIGO FORTH ===

_MARKER = '__LIST_MARKER__'

def execute(forth):
    values = []
    while forth.stack:
        v = forth.stack.pop()
        if v == _MARKER:
            forth.stack.append(values[::-1])
            return
        values.append(v)

    print("Error: |] sin [| correspondiente")
    for v in reversed(values):
        forth.stack.append(v)
