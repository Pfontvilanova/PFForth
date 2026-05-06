# FORTH CODE WORD: code/ai/text/txtwords
# Deja número de palabras en la pila

WORD_NAME = 'txt-words'
#
# === STACK EFFECT ===
# ( -- n )  Número de palabras del texto activo
# === FIN ===


def _ensure_ai(forth):
    if not hasattr(forth, '_ai'):
        forth._ai = {}
    forth._ai.setdefault('text', None)


def execute(forth):
    _ensure_ai(forth)

    text = forth._ai.get('text')
    if not text:
        print("Error: no hay texto activo — usa txt-load o txt-set primero")
        forth.stack.append(0)
        return

    n = len(text.split())
    forth.stack.append(n)
