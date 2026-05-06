# FORTH CODE WORD: code/ai/text/txtinfo
# Muestra estadísticas del texto activo

WORD_NAME = 'txt-info'
#
# === STACK EFFECT ===
# ( -- )  Muestra palabras, frases, párrafos y caracteres
# === FIN ===


def _ensure_ai(forth):
    if not hasattr(forth, '_ai'):
        forth._ai = {}
    forth._ai.setdefault('text', None)
    forth._ai.setdefault('text_path', None)
    forth._ai.setdefault('last_op', None)


def execute(forth):
    import os, re
    _ensure_ai(forth)

    text = forth._ai.get('text')
    if not text:
        print("Error: no hay texto activo — usa txt-load o txt-set primero")
        return

    path       = forth._ai.get('text_path', '')
    words      = len(text.split())
    chars      = len(text)
    sentences  = len(re.findall(r'[.!?]+', text))
    paragraphs = len([p for p in text.split('\n\n') if p.strip()])
    lines      = text.count('\n') + 1
    unique_w   = len(set(w.lower().strip('.,!?;:') for w in text.split()))

    print(f"=== Texto activo ===")
    if path:
        print(f"  Archivo    : {os.path.basename(path)}")
    print(f"  Palabras   : {words}  (únicas: {unique_w})")
    print(f"  Frases     : {sentences}")
    print(f"  Párrafos   : {paragraphs}")
    print(f"  Líneas     : {lines}")
    print(f"  Caracteres : {chars}")

    forth._ai['last_op'] = {
        'type':    'txt-info',
        'data':    {'path': path},
        'metrics': {'words': words, 'chars': chars, 'sentences': sentences,
                    'unique_words': unique_w},
    }
