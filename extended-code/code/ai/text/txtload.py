# FORTH CODE WORD: code/ai/text/txtload
# Carga un archivo de texto como texto activo

WORD_NAME = 'txt-load'
#
# === STACK EFFECT ===
# ( filename -- )  Carga fichero de texto como texto activo
# === FIN ===


def _ensure_ai(forth):
    if not hasattr(forth, '_ai'):
        forth._ai = {}
    for k, v in {
        'text': None, 'text_path': None, 'last_op': None, 'verbose': False,
    }.items():
        forth._ai.setdefault(k, v)


def execute(forth):
    import os, re
    _ensure_ai(forth)

    if not forth.stack:
        print("Error: txt-load requiere nombre de archivo en la pila")
        return

    path = str(forth.stack.pop())

    try:
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            text = f.read()
    except FileNotFoundError:
        print(f"Error: archivo no encontrado — {path}")
        return
    except Exception as e:
        print(f"Error txt-load: {e}")
        return

    forth._ai['text']      = text
    forth._ai['text_path'] = path

    words     = len(text.split())
    chars     = len(text)
    sentences = len(re.findall(r'[.!?]+', text))

    forth._ai['last_op'] = {
        'type':    'txt-load',
        'data':    {'path': path, 'filename': os.path.basename(path)},
        'metrics': {'words': words, 'chars': chars, 'sentences': sentences},
    }

    print(f"✓ Texto: {os.path.basename(path)}")
    print(f"  {words} palabras  |  {sentences} frases  |  {chars} caracteres")
