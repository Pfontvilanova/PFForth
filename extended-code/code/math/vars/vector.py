# FORTH CODE WORD: code/math/vars/vector
# Define a vector (dynamic array) variable

WORD_NAME = 'vector:'
#
# === CÓDIGO FORTH ORIGINAL ===
# ( s -- ) Create a named vector variable
# Usage: s" name" vector:
# The name becomes a word that pushes itself on the stack
# === FIN CÓDIGO FORTH ===

def execute(forth):
    if len(forth.stack) < 1:
        print("Error: vector requiere nombre")
        print('Uso: s" miVec" vector:')
        return

    name = forth.stack.pop()
    if not isinstance(name, str):
        print("Error: vector requiere un string como nombre")
        return

    if not hasattr(forth, 'vectors'):
        forth.vectors = {}

    forth.vectors[name] = []

    def word_action(n=name):
        forth.stack.append(n)

    forth.words[name] = word_action
