# FORTH CODE WORD: code/ai/explain/aiwhy
# Interpreta los resultados de la última operación AI: causas y contexto

WORD_NAME = 'ai-why'
#
# === STACK EFFECT ===
# (  -- ) Explica por qué los resultados son los que son
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
    import os, sys
    _dir = os.path.dirname(os.path.abspath(__file__))
    if _dir not in sys.path:
        sys.path.insert(0, _dir)
    import _explain_engine as _eng
    _eng.ai_why(forth)
