# FORTH CODE WORD: code/math/vars/tovec
# Build a vector from stack values

WORD_NAME = '>vec'
#
# === CÓDIGO FORTH ORIGINAL ===
# ( v1 v2 ... vn n -- vec ) Build vector from n stack values
# Usage: 10 20 30 3 >vec
# Result: [10, 20, 30]
# === FIN CÓDIGO FORTH ===

def execute(forth):
    if len(forth.stack) < 1:
        print("Error: >vec requiere n (cantidad de elementos)")
        return

    n = forth.stack.pop()
    if not isinstance(n, int) or n < 0:
        print("Error: >vec requiere un entero positivo")
        return

    if len(forth.stack) < n:
        print(f"Error: >vec necesita {n} valores en la pila")
        forth.stack.append(n)
        return

    vec = []
    for _ in range(n):
        vec.insert(0, forth.stack.pop())

    forth.stack.append(vec)
