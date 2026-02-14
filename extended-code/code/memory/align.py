# FORTH CODE WORD: code/memory/align
# Align HERE to cell boundary

WORD_NAME = 'align'
#
# === CÓDIGO FORTH ORIGINAL ===
# ( -- ) Align HERE pointer to next cell boundary
# Cell size is typically 8 bytes (64-bit)
# === FIN CÓDIGO FORTH ===

def execute(forth):
    cell_size = 8
    forth.here = (forth.here + cell_size - 1) & ~(cell_size - 1)
