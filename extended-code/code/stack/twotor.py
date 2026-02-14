# FORTH CODE WORD: code/stack/twotor
# Move two cells to return stack (2>R)

WORD_NAME = '2>r'
#
# === CÓDIGO FORTH ORIGINAL ===
# ( x1 x2 -- ) ( R: -- x1 x2 )
# Move two cells from data stack to return stack
# === FIN CÓDIGO FORTH ===

def execute(forth):
    def pop():
        if not forth.stack:
            raise IndexError("Stack underflow")
        return forth.stack.pop()
    
    if len(forth.stack) < 2:
        print("Error: 2>R requiere dos valores")
        return
    
    x2 = pop()
    x1 = pop()
    forth.rstack.append(x1)
    forth.rstack.append(x2)
