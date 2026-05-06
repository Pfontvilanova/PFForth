# FORTH CODE WORD: code/ai/text/txtset
# Usa una cadena de la pila como texto activo

WORD_NAME = 'txt-set'
#
# === STACK EFFECT ===
# ( str -- )  Establece el texto activo desde la pila
# === FIN ===


def _ensure_ai(forth):
    if not hasattr(forth, '_ai'):
        forth._ai = {}
    for k, v in {'text': None, 'text_path': None, 'last_op': None}.items():
        forth._ai.setdefault(k, v)


def execute(forth):
    _ensure_ai(forth)

    if not forth.stack:
        print("Error: txt-set requiere string en la pila")
        return

    text = str(forth.stack.pop())
    forth._ai['text']      = text
    forth._ai['text_path'] = None

    words = len(text.split())
    print(f"✓ Texto activo: {words} palabras  |  {len(text)} caracteres")
    forth._ai['last_op'] = {
        'type':    'txt-set',
        'data':    {},
        'metrics': {'words': words, 'chars': len(text)},
    }
