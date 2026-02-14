# FORTH CODE WORD: code/memory/twostore
# Store double cell to memory (2!)

WORD_NAME = '2!'
#
# === CÓDIGO FORTH ORIGINAL ===
# ( x1 x2 addr -- ) Store two cells to memory
# x2 goes to addr, x1 goes to addr+1 cell
# === FIN CÓDIGO FORTH ===

def execute(forth):
    def pop():
        if not forth.stack:
            raise IndexError("Stack underflow")
        return forth.stack.pop()
    
    if len(forth.stack) < 3:
        print("Error: 2! requiere (x1 x2 addr)")
        return
    
    addr = pop()
    x2 = pop()
    x1 = pop()
    
    if isinstance(addr, str) and addr in forth.variables:
        forth.variables[addr] = (x1, x2)
    else:
        addr = int(addr)
        if 0 <= addr < forth._memory_size:
            forth.memory[addr] = x2
        if 0 <= addr + 1 < forth._memory_size:
            forth.memory[addr + 1] = x1
