# FORTH CODE WORD: code/ai/text/txttokens
# Divide texto en tokens, devuelve lista y conteo

WORD_NAME = 'txt-tokens'
#
# === STACK EFFECT ===
# (  text -- tokens n ) Divide texto en tokens, devuelve lista y conteo
# === FIN ===


def _ensure_ai(forth):
    """Inicializa el estado AI si no existe."""
    if not hasattr(forth, '_ai'):
        forth._ai = {
            'dataset':    None,
            'target_col': None,
            'train_set':  None,
            'test_set':   None,
            'model':      None,
            'last_op':    None,
            'verbose':    False,
            'image':      None,
            'audio':      None,
            'clip_model': None,
            'yolo_model': None,
        }


def execute(forth):
    import re
    _ensure_ai(forth)

    text = forth._ai.get('text')
    if not text:
        print("Error: no hay texto activo — usa txt-load o txt-set primero")
        forth.stack.extend([[], 0])
        return

    tokens = re.findall(r'\b\w+\b', text.lower())
    n      = len(tokens)

    print(f"✓ Tokens: {n}")
    print(f"  Primeros 10: {' '.join(tokens[:10])}")

    forth._ai['last_op'] = {
        'type':    'txt-tokens',
        'data':    {},
        'metrics': {'count': n, 'unique': len(set(tokens))},
    }
    forth.stack.append(tokens)
    forth.stack.append(n)
