# FORTH CODE WORD: code/memory/charplus
# Increment address by character size (CHAR+)

WORD_NAME = 'char+'
#
# === CÓDIGO FORTH ORIGINAL ===
# ( addr -- addr+1 ) Add size of character to address
# In byte-addressed systems, this adds 1
# === FIN CÓDIGO FORTH ===

def execute(forth):
    def push(val):
        forth.stack.append(val)
    def pop():
        if not forth.stack:
            raise IndexError("Stack underflow")
        return forth.stack.pop()
    
    if len(forth.stack) < 1:
        print("Error: CHAR+ requiere una dirección")
        return
    
    addr = int(pop())
    push(addr + 1)
