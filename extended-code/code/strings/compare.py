# FORTH CODE WORD: code/strings/compare
# String comparison word
#
# === CÓDIGO FORTH ORIGINAL ===
# ( str1 str2 -- n ) Compare two strings
# Returns: -1 if str1 < str2, 0 if equal, 1 if str1 > str2
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
    
    if len(forth.stack) < 2:
        print("Error: COMPARE requiere dos cadenas")
        return
    
    top = forth.stack[-1]
    if isinstance(top, str) and isinstance(forth.stack[-2], str):
        s2 = pop()
        s1 = pop()
    elif len(forth.stack) >= 4:
        u2 = int(pop())
        a2 = pop()
        u1 = int(pop())
        a1 = pop()
        s1 = get_string(a1, u1)
        s2 = get_string(a2, u2)
    else:
        print("Error: COMPARE requiere (addr1 u1 addr2 u2) o (str1 str2)")
        return
    
    if s1 < s2:
        push(-1)
    elif s1 > s2:
        push(1)
    else:
        push(0)
