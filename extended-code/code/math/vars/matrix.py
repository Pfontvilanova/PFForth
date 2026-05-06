# FORTH CODE WORD: code/math/vars/matrix
# Define a matrix variable

WORD_NAME = 'matrix:'
#
# === CÓDIGO FORTH ORIGINAL ===
# ( s -- ) Create a named matrix variable
# Usage: s" name" matrix:
# === FIN CÓDIGO FORTH ===

def execute(forth):
    if len(forth.stack) < 1:
        print("Error: matrix: requiere nombre")
        print('Uso: s" M1" matrix:')
        return

    name = forth.stack.pop()
    if not isinstance(name, str):
        print("Error: matrix requiere un string como nombre")
        return

    if not hasattr(forth, 'vectors'):
        forth.vectors = {}

    forth.vectors[name] = None

    def word_action(n=name):
        forth.stack.append(n)

    forth.words[name] = word_action
