# FORTH CODE WORD: code/strings/slashstring
# Adjust string by skipping characters (/STRING)

WORD_NAME = '/string'
#
# === CÓDIGO FORTH ORIGINAL ===
# ( addr u n -- addr+n u-n ) or ( str n -- str2 u2 )
# Skip n characters from start of string
# === FIN CÓDIGO FORTH ===

def execute(forth):
    def push(val):
        forth.stack.append(val)
    def pop():
        if not forth.stack:
            raise IndexError("Stack underflow")
        return forth.stack.pop()
    
    if len(forth.stack) < 2:
        print("Error: /STRING requiere (str n) o (addr u n)")
        return
    
    n = int(pop())
    top = forth.stack[-1]
    
    if isinstance(top, str):
        s = pop()
        if n > len(s):
            n = len(s)
        result = s[n:]
        push(result)
        push(len(result))
    elif len(forth.stack) >= 2:
        u = int(pop())
        addr = int(pop())
        if n > u:
            n = u
        push(addr + n)
        push(u - n)
    else:
        print("Error: /STRING requiere (addr u n) o (str n)")
