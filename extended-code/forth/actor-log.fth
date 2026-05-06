\ ════════════════════════════════════════════════════════════════════
\  Módulo ACTOR-LOG — Logger centralizado para el Actor Model
\  Uso: s" actor-log" load
\
\  actor-log-start es una primitiva del sistema (actors.py).
\  Este módulo solo añade el alias corto  log  y documenta el uso.
\
\  ── Palabras disponibles (primitivas) ────────────────────────────────
\    actor-log-start ( -- log-id )    Inicia el logger (idempotente)
\    log-info  ( str -- )   Mensaje nivel INFO al logger (o stdout)
\    log-warn  ( str -- )   Mensaje nivel WARN al logger (o stdout)
\    log-error ( str -- )   Mensaje nivel ERROR al logger (o stdout)
\
\  ── Alias definido aquí ──────────────────────────────────────────────
\    log       ( str -- )   Alias de log-info para uso rápido
\
\  ── Formato de salida ────────────────────────────────────────────────
\    HH:MM:SS.mmm [INFO ] [actor-N] mensaje
\    HH:MM:SS.mmm [WARN ] [actor-N] mensaje
\    HH:MM:SS.mmm [ERROR] [actor-N] mensaje
\
\  ── Ejemplo rápido ───────────────────────────────────────────────────
\    s" actor-log" load
\    actor-log-start drop
\
\    : worker
\      s" worker arrancado" log-info
\      0 begin
\        receive
\        dup -1 = if drop exit then
\        1 + dup . cr
\      again
\      s" worker terminado" log-info ;
\
\    s" worker" spawn-run value wrk
\    10 wrk actor-send
\    -1 wrk actor-send
\    wrk actor-wait
\ ════════════════════════════════════════════════════════════════════════

\ log: alias de log-info para uso rápido
: log ( str -- )
  log-info ;

." Módulo ACTOR-LOG cargado" cr
." Primitivas: actor-log-start  log-info  log-warn  log-error" cr
." Alias:      log" cr
