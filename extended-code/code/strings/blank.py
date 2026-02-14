# FORTH CODE WORD: code/strings/blank
# Fill memory with spaces
#
# === CÓDIGO FORTH ORIGINAL ===
# ( addr u -- ) Fill memory region with spaces (ASCII 32)
# === FIN CÓDIGO FORTH ===

def execute(forth):
    def pop():
        if not forth.stack:
            raise IndexError("Stack underflow")
        return forth.stack.pop()
    
    if len(forth.stack) < 2:
        print("Error: BLANK requiere (addr u)")
        return
    
    u = int(pop())
    addr = int(pop())
    
    for i in range(u):
        if 0 <= addr + i < forth._memory_size:
            forth.memory[addr + i] = 32
