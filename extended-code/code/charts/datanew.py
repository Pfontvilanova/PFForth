# FORTH CODE WORD: code/charts/datanew
# Create or clear the data buffer

WORD_NAME = 'data-new'
#
# === CÓDIGO FORTH ORIGINAL ===
# ( -- ) Create or clear the data buffer for chart data
# === FIN CÓDIGO FORTH ===

def execute(forth):
    forth._data_buffer = []
