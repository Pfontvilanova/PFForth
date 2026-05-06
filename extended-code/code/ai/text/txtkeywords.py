# FORTH CODE WORD: code/ai/text/txtkeywords
# Extrae las n palabras clave más importantes del texto activo

WORD_NAME = 'txt-keywords'
#
# === STACK EFFECT ===
# ( n -- )  Muestra las n palabras clave del texto activo
# === FIN ===

_STOP = {
    'el','la','los','las','un','una','de','en','que','y','a','se','no','por',
    'con','para','lo','le','su','sus','es','son','del','al','pero','más',
    'como','esta','este','esto','era','fue','ser','hay','tiene','han','sido',
    'the','a','an','in','on','at','to','for','of','and','or','is','are','was',
    'were','be','been','have','has','had','it','its','this','that','with',
    'from','not','but','they','he','she','we','you','do','did','i','me','my',
    'also','about','will','can','all','one','what','which','so','if','then',
}


def _ensure_ai(forth):
    if not hasattr(forth, '_ai'):
        forth._ai = {}
    forth._ai.setdefault('text', None)
    forth._ai.setdefault('last_op', None)


def execute(forth):
    import re
    from collections import Counter
    _ensure_ai(forth)

    if not forth.stack:
        print("Error: txt-keywords requiere n en la pila  (ej: 10 txt-keywords)")
        return

    n    = max(1, int(forth.stack.pop()))
    text = forth._ai.get('text')

    if not text:
        print("Error: no hay texto activo — usa txt-load o txt-set primero")
        return

    words   = re.findall(r'\b[a-záéíóúüñA-ZÁÉÍÓÚÜÑ\w]{3,}\b', text.lower())
    filtered = [w for w in words if w not in _STOP]

    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        vec     = TfidfVectorizer(max_features=200, stop_words=None)
        mat     = vec.fit_transform([text])
        names   = vec.get_feature_names_out()
        scores  = mat.toarray()[0]
        pairs   = sorted(zip(names, scores), key=lambda x: -x[1])[:n]
        method  = 'TF-IDF'
    except Exception:
        pairs  = Counter(filtered).most_common(n)
        method = 'frecuencia'

    print(f"✓ Palabras clave ({method}, top {n}):")
    for rank, (word, score) in enumerate(pairs, 1):
        bar = '█' * int(score * 20 if method == 'TF-IDF' else min(score / (pairs[0][1] or 1) * 20, 20))
        score_str = f"{score:.4f}" if method == 'TF-IDF' else str(int(score))
        print(f"  {rank:2}. {word:<20} {bar}  ({score_str})")

    keywords = [w for w, _ in pairs]
    forth._ai['last_op'] = {
        'type':    'txt-keywords',
        'data':    {'method': method, 'n': n},
        'metrics': {'keywords': keywords},
    }
    forth.stack.append(keywords)
