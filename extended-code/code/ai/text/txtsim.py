# FORTH CODE WORD: code/ai/text/txtsim
# Similitud coseno entre dos textos

WORD_NAME = 'txt-sim'
#
# === STACK EFFECT ===
# (  text1 text2 -- similarity ) Similitud coseno entre dos textos
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

    if len(forth.stack) < 2:
        print("Error: txt-sim requiere ( str1 str2 ) en la pila")
        forth.stack.append(0.0)
        return

    str2 = str(forth.stack.pop())
    str1 = str(forth.stack.pop())

    if not str1.strip() or not str2.strip():
        print("Error: los textos no pueden estar vacíos")
        forth.stack.append(0.0)
        return

    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
        tfidf = TfidfVectorizer().fit_transform([str1, str2])
        sim   = float(cosine_similarity(tfidf[0:1], tfidf[1:2])[0][0])
        method = 'TF-IDF coseno'
    except ImportError:
        import re
        def words(t):
            return set(re.findall(r'\b\w+\b', t.lower()))
        w1, w2  = words(str1), words(str2)
        inter   = w1 & w2
        sim     = len(inter) / (len(w1 | w2) or 1)
        method  = 'Jaccard'

    sim = round(sim, 4)

    if sim >= 0.85:
        nivel = "muy similar"
    elif sim >= 0.60:
        nivel = "similar"
    elif sim >= 0.30:
        nivel = "algo parecido"
    else:
        nivel = "diferente"

    print(f"✓ Similitud: {sim:.4f}  ({nivel})  [{method}]")

    forth._ai['last_op'] = {
        'type':    'txt-sim',
        'data':    {'method': method},
        'metrics': {'score': sim},
    }
    forth.stack.append(sim)
