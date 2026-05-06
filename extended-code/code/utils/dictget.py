# FORTH CODE WORD: code/utils/dictget
# Access a key in a Python dictionary
#
# === CÓDIGO FORTH ORIGINAL ===
# ( dict key -- val )  Fetch value for key from dict
# Returns '?' if key not found
# === FIN CÓDIGO FORTH ===

WORD_NAME = 'dict@'

def execute(forth):
    def push(val):
        forth.stack.append(val)
    def pop():
        if not forth.stack:
            raise IndexError("Stack underflow")
        return forth.stack.pop()

    if len(forth.stack) < 2:
        print("Error: DICT@ requiere ( dict key )")
        return

    key = str(pop())
    d   = pop()

    try:
        push(d.get(key, '?'))
    except Exception as e:
        print(f"Error dict@: {e}")
        push('?')
