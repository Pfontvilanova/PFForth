# FORTH CODE WORD: code/ai/text/txtlang
# Detecta el idioma del texto activo

WORD_NAME = 'txt-lang'
#
# === STACK EFFECT ===
# ( -- lang )  Detecta idioma del texto activo (ej: "es", "en", "fr")
# === FIN ===

_ES = {'el','la','los','las','un','una','de','en','que','y','a','se','no',
       'por','con','para','lo','le','su','sus','es','son','del','al','pero',
       'más','como','esta','este','esto','son','era','fue','ser','hay','tiene'}
_EN = {'the','a','an','in','on','at','to','for','of','and','or','is','are',
       'was','were','be','been','have','has','had','it','its','this','that',
       'with','from','not','but','they','he','she','we','you','do','did'}
_FR = {'le','la','les','un','une','des','de','du','en','et','est','sont',
       'pour','par','sur','avec','dans','que','qui','au','aux','ne','pas'}
_DE = {'der','die','das','ein','eine','und','ist','sind','zu','mit','für',
       'von','auf','in','an','es','ich','du','er','sie','wir','nicht','hat'}
_PT = {'o','a','os','as','um','uma','de','em','que','e','é','são','por',
       'com','para','se','não','na','no','do','da','dos','das','ele','ela'}


def _ensure_ai(forth):
    if not hasattr(forth, '_ai'):
        forth._ai = {}
    forth._ai.setdefault('text', None)
    forth._ai.setdefault('last_op', None)


def _detect_lang(text):
    try:
        from langdetect import detect
        return detect(text)
    except Exception:
        pass

    words = set(text.lower().split())
    scores = {
        'es': len(words & _ES),
        'en': len(words & _EN),
        'fr': len(words & _FR),
        'de': len(words & _DE),
        'pt': len(words & _PT),
    }
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else 'unknown'


def execute(forth):
    _ensure_ai(forth)

    text = forth._ai.get('text')
    if not text:
        print("Error: no hay texto activo — usa txt-load o txt-set primero")
        forth.stack.append('unknown')
        return

    lang = _detect_lang(text[:5000])

    names = {
        'es': 'español', 'en': 'inglés', 'fr': 'francés',
        'de': 'alemán',  'pt': 'portugués', 'it': 'italiano',
    }
    name = names.get(lang, lang)
    print(f"✓ Idioma detectado: {lang}  ({name})")

    forth._ai['last_op'] = {
        'type':    'txt-lang',
        'data':    {},
        'metrics': {'lang': lang},
    }
    forth.stack.append(lang)
