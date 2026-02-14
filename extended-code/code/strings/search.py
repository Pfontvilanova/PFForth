# FORTH CODE WORD: code/strings/search
# Search substring within string
#
# === CÓDIGO FORTH ORIGINAL ===
# ( str1 str2 -- str3 u3 flag ) Search for str2 within str1
# If found: returns match string, length, true (-1)
# If not found: returns original, length, false (0)
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
        print("Error: SEARCH requiere dos cadenas")
        return
    
    top = forth.stack[-1]
    if isinstance(top, str) and isinstance(forth.stack[-2], str):
        needle = pop()
        haystack = pop()
    elif len(forth.stack) >= 4:
        u2 = int(pop())
        a2 = pop()
        u1 = int(pop())
        a1 = pop()
        haystack = get_string(a1, u1)
        needle = get_string(a2, u2)
    else:
        print("Error: SEARCH requiere (addr1 u1 addr2 u2) o (str1 str2)")
        return
    
    pos = haystack.find(needle)
    if pos >= 0:
        remaining = haystack[pos:]
        push(remaining)
        push(len(remaining))
        push(-1)
    else:
        push(haystack)
        push(len(haystack))
        push(0)
