# FORTH CODE WORD: code/graphics/cursoroff
# Hide terminal cursor

WORD_NAME = 'cursor-off'
#
# === CÓDIGO FORTH ORIGINAL ===
# ( -- ) Hide the terminal cursor
# === FIN CÓDIGO FORTH ===

import sys

def execute(forth):
    sys.stdout.write("\033[?25l")
    sys.stdout.flush()
