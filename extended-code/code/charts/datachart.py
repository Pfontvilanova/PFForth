# FORTH CODE WORD: code/charts/datachart
# Push all data buffer values and count to stack

WORD_NAME = 'data-chart'
#
# === CÓDIGO FORTH ORIGINAL ===
# ( -- v1 v2 ... vn n ) Push all buffer values then count to stack
# Ready to pass to any chart word: data-chart bar-chart
# === FIN CÓDIGO FORTH ===

def execute(forth):
    buf = getattr(forth, '_data_buffer', [])
    if not buf:
        print("Error: buffer de datos vacio (usa data-new y data-add)")
        return
    for v in buf:
        forth.stack.append(v)
    forth.stack.append(len(buf))
