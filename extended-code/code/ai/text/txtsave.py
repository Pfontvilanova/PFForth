# FORTH CODE WORD: code/ai/text/txtsave
# Guarda el texto activo en un archivo

WORD_NAME = 'txt-save'
#
# === STACK EFFECT ===
# ( filename -- )  Guarda el texto activo en filename
# === FIN ===


def _ensure_ai(forth):
    if not hasattr(forth, '_ai'):
        forth._ai = {}
    forth._ai.setdefault('text', None)
    forth._ai.setdefault('last_op', None)


def execute(forth):
    import os
    _ensure_ai(forth)

    if not forth.stack:
        print("Error: txt-save requiere nombre de archivo en la pila")
        return

    path = str(forth.stack.pop())
    text = forth._ai.get('text')

    if not text:
        print("Error: no hay texto activo — usa txt-load o txt-set primero")
        return

    try:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(text)
        size = os.path.getsize(path)
        print(f"✓ Guardado: {os.path.basename(path)}  ({size} bytes)")
        forth._ai['text_path'] = path
        forth._ai['last_op'] = {
            'type':    'txt-save',
            'data':    {'path': path},
            'metrics': {'bytes': size},
        }
    except Exception as e:
        print(f"Error txt-save: {e}")
