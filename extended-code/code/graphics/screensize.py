# FORTH CODE WORD: code/graphics/screensize
# Get terminal size

WORD_NAME = 'screen-size'
#
# === CÓDIGO FORTH ORIGINAL ===
# ( -- cols rows ) Push terminal width and height to stack
# === FIN CÓDIGO FORTH ===

import shutil

def execute(forth):
    size = shutil.get_terminal_size((80, 24))
    forth.stack.append(size.columns)
    forth.stack.append(size.lines)
