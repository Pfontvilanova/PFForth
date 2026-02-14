# FORTH CODE WORD: code/strings/trailing
# Remove trailing spaces (-TRAILING)

WORD_NAME = '-trailing'
#
# === CÓDIGO FORTH ORIGINAL ===
# ( addr u1 -- addr u2 ) or ( str -- str2 u2 )
# Remove trailing spaces from string
# === FIN CÓDIGO FORTH ===

def execute(forth):
    def push(val):
        forth.stack.append(val)
    def pop():
        if not forth.stack:
            raise IndexError("Stack underflow")
        return forth.stack.pop()
    
    def get_string(addr, length):
        if isinstance(addr, str):
            return addr[:length] if length < len(addr) else addr
        addr = int(addr)
        chars = []
        for i in range(length):
            if 0 <= addr + i < forth._memory_size:
                val = forth.memory[addr + i]
                if isinstance(val, int):
                    chars.append(chr(val))
        return ''.join(chars)
    
    if len(forth.stack) < 1:
        print("Error: -TRAILING requiere una cadena")
        return
    
    top = forth.stack[-1]
    if isinstance(top, str):
        s = pop()
        result = s.rstrip(' ')
        push(result)
        push(len(result))
    elif len(forth.stack) >= 2:
        u = int(pop())
        addr = pop()
        s = get_string(addr, u)
        result = s.rstrip(' ')
        push(addr)
        push(len(result))
    else:
        print("Error: -TRAILING requiere (addr u) o (str)")
