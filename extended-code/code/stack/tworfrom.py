# FORTH CODE WORD: code/stack/tworfrom
# Move two cells from return stack (2R>)

WORD_NAME = '2r>'
#
# === CÓDIGO FORTH ORIGINAL ===
# ( -- x1 x2 ) ( R: x1 x2 -- )
# Move two cells from return stack to data stack
# === FIN CÓDIGO FORTH ===

def execute(forth):
    def push(val):
        forth.stack.append(val)
    
    if len(forth.rstack) < 2:
        print("Error: 2R> requiere dos valores en return stack")
        return
    
    x2 = forth.rstack.pop()
    x1 = forth.rstack.pop()
    push(x1)
    push(x2)
