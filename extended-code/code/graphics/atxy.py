# FORTH CODE WORD: code/graphics/atxy
# Move cursor to position x, y

WORD_NAME = 'at-xy'
#
# === CÓDIGO FORTH ORIGINAL ===
# ( x y -- ) Move cursor to column x, row y (0-based)
# === FIN CÓDIGO FORTH ===

import sys

def execute(forth):
    if len(forth.stack) < 2:
        print("Error: at-xy requiere x y")
        return
    y = forth.stack.pop()
    x = forth.stack.pop()
    sys.stdout.write(f"\033[{y+1};{x+1}H")
    sys.stdout.flush()
