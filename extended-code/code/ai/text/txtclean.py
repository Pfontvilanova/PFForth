# FORTH CODE WORD: code/ai/text/txtclean
# Limpia y normaliza el texto activo

WORD_NAME = 'txt-clean'
#
# === STACK EFFECT ===
# ( -- )  Limpia texto activo: minúsculas, sin puntuación extra, espacios normalizados
# === FIN ===


def _ensure_ai(forth):
    if not hasattr(forth, '_ai'):
        forth._ai = {}
    forth._ai.setdefault('text', None)
    forth._ai.setdefault('last_op', None)


def execute(forth):
    import re
    _ensure_ai(forth)

    text = forth._ai.get('text')
    if not text:
        print("Error: no hay texto activo — usa txt-load o txt-set primero")
        return

    original_len  = len(text)

    text = text.lower()
    text = re.sub(r'https?://\S+', ' ', text)
    text = re.sub(r'[^\w\s\.\,\!\?\;\:\-]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()

    forth._ai['text'] = text
    new_len = len(text)

    print(f"✓ Texto limpiado")
    print(f"  Antes: {original_len} chars  →  Ahora: {new_len} chars")

    forth._ai['last_op'] = {
        'type':    'txt-clean',
        'data':    {},
        'metrics': {'before': original_len, 'after': new_len},
    }
