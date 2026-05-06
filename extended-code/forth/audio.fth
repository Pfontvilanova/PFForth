\ ════════════════════════════════════════════════════════
\  Módulo AUDIO — Análisis de audio con pfforth
\  Uso: s" audio" load
\
\  ── Cargar / guardar ─────────────────────────────────────
\    aud-load      ( filename -- )   Carga .wav/.mp3/.flac como activo
\    aud-save      ( filename -- )   Guarda audio activo en disco
\
\  ── Información ─────────────────────────────────────────
\    aud-info      ( -- )            Duración, SR, amplitud
\    aud-duration  ( -- seconds )    Duración en segundos en la pila
\
\  ── Visualización ────────────────────────────────────────
\    aud-waveform  ( -- )            Forma de onda ASCII en terminal
\    aud-spectro   ( -- )            Espectrograma ASCII en terminal
\
\  ── Características ──────────────────────────────────────
\    aud-features  ( -- vec )        13 MFCCs (media) + ZCR + centroide
\    aud-tempo     ( -- bpm )        Tempo en BPM
\    aud-pitch     ( -- hz )         Frecuencia fundamental en Hz
\
\  ── Transformaciones ─────────────────────────────────────
\    aud-trim      ( -- )            Elimina silencio inicial/final
\
\  ── Clasificación y transcripción ────────────────────────
\    aud-classify  ( -- label conf ) Clasifica: speech/music/noise/silence
\    aud-transcribe ( -- text )      Voz a texto (Whisper o SR)
\ ════════════════════════════════════════════════════════

import code/ai/audio

." Módulo AUDIO cargado — 12 palabras" cr
