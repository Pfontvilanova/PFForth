# FORTH CODE WORD: code/ai/audio/audclassify
# Clasifica el tipo de audio: voz, música, silencio, ruido

WORD_NAME = 'aud-classify'
#
# === STACK EFFECT ===
# ( -- label confidence )  Clasifica tipo de audio activo
# === FIN ===


def _ensure_ai(forth):
    if not hasattr(forth, '_ai'):
        forth._ai = {}
    forth._ai.setdefault('audio', None)
    forth._ai.setdefault('last_op', None)


def _classify_heuristic(y, sr):
    import numpy as np

    try:
        import librosa
        zcr      = float(np.mean(librosa.feature.zero_crossing_rate(y)))
        sc       = float(np.mean(librosa.feature.spectral_centroid(y=y, sr=sr)))
        rolloff  = float(np.mean(librosa.feature.spectral_rolloff(y=y, sr=sr)))
        rms      = float(np.sqrt(np.mean(y ** 2)))
        flatness = float(np.mean(librosa.feature.spectral_flatness(y=y)))
    except ImportError:
        return 'unknown', 0.5

    if rms < 0.005:
        return 'silence', 0.95

    scores = {
        'speech': 0.0,
        'music':  0.0,
        'noise':  0.0,
    }

    if 1500 < sc < 3500 and 0.05 < zcr < 0.20:
        scores['speech'] += 2.0
    if 0.05 < zcr < 0.15:
        scores['speech'] += 0.5

    if sc > 3000 and zcr < 0.12 and rolloff > 4000:
        scores['music'] += 2.0
    if rolloff > 6000:
        scores['music'] += 0.5

    if flatness > 0.3:
        scores['noise'] += 2.0
    if zcr > 0.25:
        scores['noise'] += 1.0

    label = max(scores, key=scores.get)
    total = sum(scores.values()) or 1.0
    conf  = round(scores[label] / total, 3)
    return label, conf


def execute(forth):
    _ensure_ai(forth)

    audio = forth._ai.get('audio')
    if audio is None:
        print("Error: no hay audio activo — usa aud-load primero")
        forth.stack.extend(['unknown', 0.0])
        return

    y, sr = audio

    label, conf = _classify_heuristic(y, sr)

    icons = {'speech': '🎤', 'music': '🎵', 'noise': '📢', 'silence': '🔇', 'unknown': '?'}
    icon  = icons.get(label, '')
    names_es = {'speech': 'voz', 'music': 'música', 'noise': 'ruido',
                'silence': 'silencio', 'unknown': 'desconocido'}
    name_es = names_es.get(label, label)
    print(f"✓ Tipo de audio: {label} ({name_es})  conf={conf:.3f}  {icon}")

    forth._ai['last_op'] = {
        'type':    'aud-classify',
        'data':    {},
        'metrics': {'label': label, 'confidence': conf},
    }
    forth.stack.append(label)
    forth.stack.append(conf)
