# FORTH CODE WORD: code/graphics/resetcolor
# Reset terminal colors to default

WORD_NAME = 'reset-color'
#
# === CÓDIGO FORTH ORIGINAL ===
# ( -- ) Reset all colors and attributes to default
# === FIN CÓDIGO FORTH ===

import sys

def execute(forth):
    sys.stdout.write("\033[0m")
    sys.stdout.flush()
