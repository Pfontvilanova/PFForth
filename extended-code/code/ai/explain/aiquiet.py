# FORTH CODE WORD: code/ai/explain/aiquiet
# Desactiva las explicaciones automáticas tras cada operación AI

WORD_NAME = 'ai-quiet'
#
# === STACK EFFECT ===
# (  -- ) Desactiva el modo verbose: salida mínima tras cada operación AI
# === FIN ===


def _ensure_ai(forth):
    if not hasattr(forth, '_ai'):
        forth._ai = {
            'dataset': None, 'target_col': None,
            'train_set': None, 'test_set': None,
            'model': None, 'last_op': None, 'verbose': False,
            'image': None, 'audio': None,
            'clip_model': None, 'yolo_model': None,
        }


def execute(forth):
    _ensure_ai(forth)
    forth._ai['verbose'] = False
    print("Modo quiet activado — salida mínima. Usa ai-verbose para más detalle.")
