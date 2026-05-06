# FORTH CODE WORD: code/ai/data/aireset
# Limpia el estado del entorno AI

WORD_NAME = 'ai-reset'
#
# === STACK EFFECT ===
# ( -- ) Limpia todo el estado AI: datos, modelo, imágenes y última operación
#        Mantiene la configuración (verbose, modelos CLIP/YOLO ya cargados)
#        Para limpiar también modelos: s" all" ai-reset
# === FIN ===

_EMPTY_STATE = {
    'dataset': None, 'target_col': None,
    'train_set': None, 'test_set': None,
    'model': None, 'last_op': None,
    'image': None, 'audio': None,
    'scaler': None,
}


def _ensure_ai(forth):
    if not hasattr(forth, '_ai'):
        forth._ai = {
            'dataset': None, 'target_col': None,
            'train_set': None, 'test_set': None,
            'model': None, 'last_op': None,
            'verbose': False, 'image': None,
            'audio': None, 'clip_model': None, 'yolo_model': None,
            'scaler': None,
        }


def execute(forth):
    _ensure_ai(forth)
    ai = forth._ai

    # Comprueba si el usuario quiere reset total (incluye modelos pesados)
    full = False
    if forth.stack and forth.stack[-1] == 'all':
        forth.stack.pop()
        full = True

    cleared = []

    if ai.get('dataset') is not None:
        cleared.append('dataset')
    if ai.get('train_set') is not None or ai.get('test_set') is not None:
        cleared.append('split')
    if ai.get('model') is not None:
        cleared.append('modelo')
    if ai.get('image') is not None:
        cleared.append('imagen')
    if ai.get('audio') is not None:
        cleared.append('audio')
    if ai.get('scaler') is not None:
        cleared.append('scaler')

    # Aplicar reset
    for key, val in _EMPTY_STATE.items():
        ai[key] = val

    if full:
        if ai.get('clip_model') is not None:
            cleared.append('CLIP')
            ai['clip_model'] = None
        if ai.get('yolo_model') is not None:
            cleared.append('YOLO')
            ai['yolo_model'] = None

    if cleared:
        print(f"✓ Reset: {', '.join(cleared)} liberados")
    else:
        print("  El entorno ya estaba vacío — nada que limpiar")

    if not full and (ai.get('clip_model') or ai.get('yolo_model')):
        models = []
        if ai.get('clip_model'): models.append('CLIP')
        if ai.get('yolo_model'): models.append('YOLO')
        print(f"  (modelos {', '.join(models)} conservados — usa s\" all\" ai-reset para liberarlos)")
