# FORTH CODE WORD: code/charts/dataadd
# Add a value to the data buffer

WORD_NAME = 'data-add'
#
# === CÓDIGO FORTH ORIGINAL ===
# ( v -- ) Add value to the data buffer
# === FIN CÓDIGO FORTH ===

def execute(forth):
    if len(forth.stack) < 1:
        print("Error: data-add requiere un valor")
        return
    v = forth.stack.pop()
    if not hasattr(forth, '_data_buffer'):
        forth._data_buffer = []
    forth._data_buffer.append(v)
