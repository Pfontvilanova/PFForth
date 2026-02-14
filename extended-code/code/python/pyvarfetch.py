# FORTH CODE WORD: code/python/pyvarfetch
# Fetch value from shared Python variable

WORD_NAME = 'py-var@'
#
# === CÓDIGO FORTH ORIGINAL ===
# ( name -- value ) Fetch value from shared Python/Forth variable
# === FIN CÓDIGO FORTH ===

def execute(forth):
    def push(val):
        forth.stack.append(val)
    def pop():
        if not forth.stack:
            raise IndexError("Stack underflow")
        return forth.stack.pop()
    
    if len(forth.stack) < 1:
        print("Error: PY-VAR@ requiere nombre")
        return
    
    name = str(pop())
    
    if not hasattr(forth, 'shared'):
        forth.shared = {}
    
    if name in forth.shared:
        push(forth.shared[name])
    else:
        print(f"Error: Variable '{name}' no existe")
        push(0)
