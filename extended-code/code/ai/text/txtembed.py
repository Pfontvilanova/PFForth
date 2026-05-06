# FORTH CODE WORD: code/ai/text/txtembed
# Genera embedding de oración con sentence-transformers

WORD_NAME = 'txt-embed'
#
# === STACK EFFECT ===
# (  text -- vec ) Genera embedding de oración con sentence-transformers
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
    _ensure_ai(forth)

    text = forth._ai.get('text')
    if not text:
        print("Error: no hay texto activo — usa txt-load o txt-set primero")
        forth.stack.append(None)
        return

    try:
        from sentence_transformers import SentenceTransformer
        model = forth._ai.get('_st_model')
        if model is None:
            print("Cargando sentence-transformers (primera vez ~90 MB)...")
            model = SentenceTransformer('all-MiniLM-L6-v2')
            forth._ai['_st_model'] = model
        vec    = model.encode(text).tolist()
        method = 'sentence-transformers'
    except ImportError:
        from sklearn.feature_extraction.text import TfidfVectorizer
        vec    = TfidfVectorizer(max_features=512).fit_transform([text]).toarray()[0].tolist()
        method = 'TF-IDF'

    dims = len(vec)
    forth._ai['text_embedding'] = vec
    forth._ai['last_op'] = {
        'type':    'txt-embed',
        'data':    {'method': method},
        'metrics': {'dims': dims},
    }
    print(f"✓ Embedding ({method}): {dims} dimensiones")
    forth.stack.append(vec)
