# FORTH CODE WORD: code/memory/twofetch
# Fetch double cell from memory (2@)

WORD_NAME = '2@'
#
# === CÓDIGO FORTH ORIGINAL ===
# ( addr -- x1 x2 ) Fetch two cells from memory
# x2 is at addr, x1 is at addr+1 cell
# === FIN CÓDIGO FORTH ===

def execute(forth):
    def push(val):
        forth.stack.append(val)
    def pop():
        if not forth.stack:
            raise IndexError("Stack underflow")
        return forth.stack.pop()
    
    if len(forth.stack) < 1:
        print("Error: 2@ requiere una dirección")
        return
    
    addr = pop()
    
    if isinstance(addr, str) and addr in forth.variables:
        val = forth.variables[addr]
        if isinstance(val, tuple) and len(val) == 2:
            push(val[0])
            push(val[1])
        else:
            push(val)
            push(0)
    else:
        addr = int(addr)
        x2 = forth.memory[addr] if 0 <= addr < forth._memory_size else 0
        x1 = forth.memory[addr + 1] if 0 <= addr + 1 < forth._memory_size else 0
        push(x1)
        push(x2)
