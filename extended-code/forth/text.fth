\ ════════════════════════════════════════════════════════
\  Módulo TEXT — Análisis y procesamiento de texto
\  Uso: s" text" load
\
\  ── Cargar / establecer ──────────────────────────────────
\    txt-load    ( filename -- )      Carga fichero de texto como activo
\    txt-set     ( str -- )           Establece texto desde la pila
\    txt-save    ( filename -- )      Guarda texto activo en fichero
\
\  ── Información ─────────────────────────────────────────
\    txt-info    ( -- )               Estadísticas: palabras, frases, chars
\    txt-words   ( -- n )             Número de palabras en la pila
\    txt-lang    ( -- lang )          Detecta idioma ("es","en","fr"…)
\
\  ── Procesamiento ────────────────────────────────────────
\    txt-clean   ( -- )               Limpia y normaliza el texto activo
\    txt-tokens  ( -- tokens n )      Lista de tokens y conteo
\    txt-keywords ( n -- )            Top n palabras clave
\
\  ── Análisis ─────────────────────────────────────────────
\    txt-sentiment ( -- label score ) Positivo/negativo/neutro
\    txt-summary   ( n -- )           Resumen extractivo en n frases
\    txt-sim       ( str1 str2 -- f ) Similitud coseno entre dos textos
\
\  ── Representación vectorial ────────────────────────────
\    txt-embed   ( -- vec )           Vector de embedding (TF-IDF o ST)
\
\  ── Generación (requiere transformers) ──────────────────
\    txt-generate ( prompt maxlen -- text )  Genera texto con GPT-2
\ ════════════════════════════════════════════════════════

import code/ai/text

." Módulo TEXT cargado — 14 palabras" cr
