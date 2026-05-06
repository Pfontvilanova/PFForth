# FORTH CODE WORD: code/graphics/color
# Set text foreground color

WORD_NAME = 'color'
#
# === CÓDIGO FORTH ORIGINAL ===
# ( n -- ) Set text color (0-15)
# 0=black 1=red 2=green 3=yellow 4=blue 5=magenta 6=cyan 7=white
# 8-15 = bright versions
# === FIN CÓDIGO FORTH ===

import sys

def execute(forth):
    if len(forth.stack) < 1:
        print("Error: color requiere n (0-15)")
        return
    n = forth.stack.pop()
    if 0 <= n <= 7:
        sys.stdout.write(f"\033[3{n}m")
    elif 8 <= n <= 15:
        sys.stdout.write(f"\033[9{n-8}m")
    else:
        print(f"Error: color {n} fuera de rango (0-15)")
        return
    sys.stdout.flush()
