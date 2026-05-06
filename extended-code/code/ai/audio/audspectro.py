# FORTH CODE WORD: code/ai/audio/audspectro
# Muestra espectrograma ASCII en terminal

WORD_NAME = 'aud-spectro'
#
# === STACK EFFECT ===
# ( -- )  Espectrograma de magnitud en terminal (bloques Unicode)
# === FIN ===

_BLOCKS = ' ▁▂▃▄▅▆▇█'


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
        return

    y, sr = audio

    try:
        import librosa
        import numpy as np

        cols   = 72
        rows   = 12
        D      = np.abs(librosa.stft(y, n_fft=2048, hop_length=512))
        D_db   = librosa.amplitude_to_db(D, ref=np.max)

        n_bins  = D_db.shape[0]
        n_frames = D_db.shape[1]

        freq_step  = max(1, n_bins  // rows)
        time_step  = max(1, n_frames // cols)

        mat = np.zeros((rows, cols))
        for r in range(rows):
            for c in range(cols):
                fb = r * freq_step
                fe = min(fb + freq_step, n_bins)
                tb = c * time_step
                te = min(tb + time_step, n_frames)
                mat[r, c] = D_db[fb:fe, tb:te].mean()

        vmin, vmax = mat.min(), mat.max()
        rng = vmax - vmin or 1.0

        duration = len(y) / sr
        print(f"=== Espectrograma ({duration:.1f}s  |  {sr} Hz) ===")
        print(f"  alta freq  {'─' * cols}")
        for r in range(rows - 1, -1, -1):
            row_str = ''
            for c in range(cols):
                idx = int((mat[r, c] - vmin) / rng * 8)
                row_str += _BLOCKS[max(0, min(8, idx))]
            hz = int((r + 0.5) * freq_step * sr / 2 / n_bins)
            print(f"  {hz:5d}Hz  {row_str}")
        print(f"  baja freq  {'─' * cols}")
        print(f"  {'0s':^10}{'→':^{cols - 20}}{duration:.1f}s")

    except ImportError:
        print("Error: aud-spectro requiere librosa")
        print("  pip install librosa")
        return

    forth._ai['last_op'] = {
        'type':    'aud-spectro',
        'data':    {},
        'metrics': {'rows': rows, 'cols': cols},
    }
