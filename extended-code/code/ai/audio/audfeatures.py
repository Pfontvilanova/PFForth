# FORTH CODE WORD: code/ai/audio/audfeatures
# Extrae MFCCs y espectro del audio activo

WORD_NAME = 'aud-features'
#
# === STACK EFFECT ===
# ( -- vec )  Extrae 13 MFCCs (media) y los deja en la pila como lista
# === FIN ===


def _ensure_ai(forth):
    if not hasattr(forth, '_ai'):
        forth._ai = {}
    forth._ai.setdefault('audio', None)
    forth._ai.setdefault('last_op', None)


def execute(forth):
    _ensure_ai(forth)

    audio = forth._ai.get('audio')
    if audio is None:
        print("Error: no hay audio activo — usa aud-load primero")
        forth.stack.append(None)
        return

    y, sr = audio

    try:
        import librosa
        import numpy as np
        mfcc          = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
        mfcc_mean     = np.mean(mfcc, axis=1)
        zcr           = float(np.mean(librosa.feature.zero_crossing_rate(y)))
        sc            = float(np.mean(librosa.feature.spectral_centroid(y=y, sr=sr)))
        rolloff       = float(np.mean(librosa.feature.spectral_rolloff(y=y, sr=sr)))
        features      = mfcc_mean.tolist() + [zcr, sc, rolloff]
    except ImportError:
        print("Error: aud-features requiere librosa")
        print("  pip install librosa")
        forth.stack.append(None)
        return

    print(f"✓ Features extraídas: {len(features)} valores")
    print(f"  MFCC (13): {' '.join(f'{v:.2f}' for v in features[:13])}")
    print(f"  ZCR={zcr:.4f}  SpCentroid={sc:.1f} Hz  Rolloff={rolloff:.1f} Hz")

    forth._ai['audio_features'] = features
    forth._ai['last_op'] = {
        'type':    'aud-features',
        'data':    {'n_mfcc': 13},
        'metrics': {'dims': len(features), 'zcr': round(zcr, 4),
                    'spectral_centroid': round(sc, 1)},
    }
    forth.stack.append(features)
