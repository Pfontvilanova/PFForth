# FORTH CODE WORD: code/ai/explain/aiverbose
# Activa explicaciones automáticas tras cada operación AI

WORD_NAME = 'ai-verbose'
#
# === STACK EFFECT ===
# (  -- ) Activa el modo verbose: cada operación AI imprime una narrativa breve
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
    forth._ai['verbose'] = True
    print("Modo verbose activado — las operaciones AI mostrarán explicaciones automáticas.")
    print("Usa ai-quiet para desactivarlo.")
