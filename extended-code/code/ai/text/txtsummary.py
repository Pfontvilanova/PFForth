# FORTH CODE WORD: code/ai/text/txtsummary
# Resumen extractivo del texto activo

WORD_NAME = 'txt-summary'
#
# === STACK EFFECT ===
# ( n -- )  Muestra resumen del texto activo en n frases
# === FIN ===


def _ensure_ai(forth):
    if not hasattr(forth, '_ai'):
        forth._ai = {}
    forth._ai.setdefault('text', None)
    forth._ai.setdefault('last_op', None)


def _extractive_summary(text, n):
    import re
    from collections import Counter

    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    if len(sentences) <= n:
        return sentences

    stopwords = {
        'el','la','los','las','un','una','de','en','que','y','a','se','no','por','con',
        'para','lo','le','su','sus','es','son','del','al','una','pero','más','como',
        'the','a','an','in','on','at','to','for','of','and','or','is','are','was',
        'were','be','been','have','has','had','it','its','this','that','with','from',
    }

    words  = re.findall(r'\b\w+\b', text.lower())
    freq   = Counter(w for w in words if w not in stopwords and len(w) > 2)

    def score(sent):
        ws = re.findall(r'\b\w+\b', sent.lower())
        return sum(freq.get(w, 0) for w in ws) / (len(ws) or 1)

    ranked    = sorted(enumerate(sentences), key=lambda x: -score(x[1]))
    top_idx   = sorted(i for i, _ in ranked[:n])
    return [sentences[i] for i in top_idx]


def execute(forth):
    _ensure_ai(forth)

    if not forth.stack:
        print("Error: txt-summary requiere n en la pila  (ej: 3 txt-summary)")
        return

    n    = max(1, int(forth.stack.pop()))
    text = forth._ai.get('text')

    if not text:
        print("Error: no hay texto activo — usa txt-load o txt-set primero")
        return

    summary = _extractive_summary(text, n)

    print(f"✓ Resumen ({len(summary)} frases):")
    for i, s in enumerate(summary, 1):
        print(f"  {i}. {s.strip()}")

    result = ' '.join(summary)
    forth._ai['last_op'] = {
        'type':    'txt-summary',
        'data':    {'n_requested': n},
        'metrics': {'sentences_out': len(summary)},
    }
    forth.stack.append(result)
