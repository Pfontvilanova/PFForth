# FORTH CODE WORD: code/charts/datacount
# Push data buffer count to stack

WORD_NAME = 'data-count'
#
# === CÓDIGO FORTH ORIGINAL ===
# ( -- n ) Push the number of values in the data buffer
# === FIN CÓDIGO FORTH ===

def execute(forth):
    buf = getattr(forth, '_data_buffer', [])
    forth.stack.append(len(buf))
