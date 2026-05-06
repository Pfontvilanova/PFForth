# FORTH CODE WORD: code/graphics/bgcolor
# Set text background color

WORD_NAME = 'bg-color'
#
# === CÓDIGO FORTH ORIGINAL ===
# ( n -- ) Set background color (0-15)
# 0=black 1=red 2=green 3=yellow 4=blue 5=magenta 6=cyan 7=white
# 8-15 = bright versions
# === FIN CÓDIGO FORTH ===

import sys

def execute(forth):
    if len(forth.stack) < 1:
        print("Error: bg-color requiere n (0-15)")
        return
    n = forth.stack.pop()
    if 0 <= n <= 7:
        sys.stdout.write(f"\033[4{n}m")
    elif 8 <= n <= 15:
        sys.stdout.write(f"\033[10{n-8}m")
    else:
        print(f"Error: bg-color {n} fuera de rango (0-15)")
        return
    sys.stdout.flush()
