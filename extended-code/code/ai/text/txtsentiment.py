# FORTH CODE WORD: code/ai/text/txtsentiment
# Sentimiento: positivo/negativo/neutro + puntuación

WORD_NAME = 'txt-sentiment'
#
# === STACK EFFECT ===
# ( -- label score )  Analiza sentimiento del texto activo
#                     label: "positive" / "negative" / "neutral"
#                     score: 0.0 – 1.0
# === FIN ===

_POS = {
    'good','great','excellent','amazing','wonderful','best','love','happy','perfect',
    'fantastic','superb','outstanding','brilliant','awesome','nice','enjoy','pleased',
    'bueno','excelente','maravilloso','genial','feliz','perfecto','increíble','mejor',
    'positivo','favorable','óptimo','estupendo','encantado','satisfecho','recomendable',
}
_NEG = {
    'bad','terrible','awful','horrible','worst','hate','poor','disappointing','wrong',
    'problem','fail','failure','broken','useless','annoying','frustrated','ugly',
    'malo','terrible','pésimo','horrible','peor','odio','problema','feo','roto',
    'negativo','desastroso','decepcionante','frustrado','inútil','lamentable',
}


def _ensure_ai(forth):
    if not hasattr(forth, '_ai'):
        forth._ai = {}
    forth._ai.setdefault('text', None)
    forth._ai.setdefault('last_op', None)


def _simple_sentiment(text):
    words = set(text.lower().split())
    pos   = len(words & _POS)
    neg   = len(words & _NEG)
    total = pos + neg or 1
    if pos > neg:
        return 'positive', round(pos / total, 3)
    elif neg > pos:
        return 'negative', round(neg / total, 3)
    else:
        return 'neutral', 0.5


def execute(forth):
    _ensure_ai(forth)

    text = forth._ai.get('text')
    if not text:
        print("Error: no hay texto activo — usa txt-load o txt-set primero")
        forth.stack.extend(['neutral', 0.0])
        return

    try:
        from textblob import TextBlob
        blob     = TextBlob(text)
        polarity = blob.sentiment.polarity
        if polarity > 0.05:
            label, score = 'positive', round(polarity, 3)
        elif polarity < -0.05:
            label, score = 'negative', round(abs(polarity), 3)
        else:
            label, score = 'neutral', round(abs(polarity), 3)
        method = 'TextBlob'
    except ImportError:
        label, score = _simple_sentiment(text)
        method = 'léxico propio'

    icons = {'positive': '+', 'negative': '-', 'neutral': '~'}
    print(f"✓ Sentimiento: {label}  ({score:.3f})  [{icons.get(label,'')}]  [{method}]")

    forth._ai['last_op'] = {
        'type':    'txt-sentiment',
        'data':    {'method': method},
        'metrics': {'label': label, 'score': score},
    }
    forth.stack.append(label)
    forth.stack.append(score)
