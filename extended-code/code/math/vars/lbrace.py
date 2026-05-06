# FORTH CODE WORD: code/math/vars/lbrace
# Start list literal - pushes a marker

WORD_NAME = '[|'
#
# === CÓDIGO FORTH ORIGINAL ===
# ( -- marker ) Push list start marker
# Usage: [| 1 2 3 |] v1 v!
# === FIN CÓDIGO FORTH ===

_MARKER = '__LIST_MARKER__'

def execute(forth):
    forth.stack.append(_MARKER)
