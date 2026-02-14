# FORTH CODE WORD: code/python/pyvarstore
# Store value in shared Python variable

WORD_NAME = 'py-var!'
#
# === CÓDIGO FORTH ORIGINAL ===
# ( value name -- ) Store value in shared Python/Forth variable
# === FIN CÓDIGO FORTH ===

def execute(forth):
    def pop():
        if not forth.stack:
            raise IndexError("Stack underflow")
        return forth.stack.pop()
    
    if len(forth.stack) < 2:
        print("Error: PY-VAR! requiere valor y nombre")
        return
    
    name = str(pop())
    value = pop()
    
    if not hasattr(forth, 'shared'):
        forth.shared = {}
    
    forth.shared[name] = value
