# FORTH CODE WORD: code/graphics/cursoron
# Show terminal cursor

WORD_NAME = 'cursor-on'
#
# === CÓDIGO FORTH ORIGINAL ===
# ( -- ) Show the terminal cursor
# === FIN CÓDIGO FORTH ===

import sys

def execute(forth):
    sys.stdout.write("\033[?25h")
    sys.stdout.flush()
