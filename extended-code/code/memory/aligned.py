# FORTH CODE WORD: code/memory/aligned
# Align address to cell boundary

WORD_NAME = 'aligned'
#
# === CÓDIGO FORTH ORIGINAL ===
# ( addr -- addr' ) Align address to next cell boundary
# Cell size is typically 8 bytes (64-bit)
# === FIN CÓDIGO FORTH ===

def execute(forth):
    def push(val):
        forth.stack.append(val)
    def pop():
        if not forth.stack:
            raise IndexError("Stack underflow")
        return forth.stack.pop()
    
    if len(forth.stack) < 1:
        print("Error: ALIGNED requiere una dirección")
        return
    
    addr = int(pop())
    cell_size = 8
    aligned_addr = (addr + cell_size - 1) & ~(cell_size - 1)
    push(aligned_addr)
