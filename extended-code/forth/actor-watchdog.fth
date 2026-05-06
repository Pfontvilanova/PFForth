\ ════════════════════════════════════════════════════════════════════
\  Módulo ACTOR-WATCHDOG — Supervisión automática de actores
\  Uso: s" actor-watchdog" load
\
\  Supervisa un actor y lo reinicia automáticamente si falla o termina
\  de forma inesperada. Integrado con actor-log si está activo.
\
\  ── Palabra principal ─────────────────────────────────────────────────
\    actor-watchdog ( interval-ms max-retries actor-id -- watchdog-id )
\
\      interval-ms   — cada cuántos ms comprueba si el actor sigue vivo
\      max-retries   — máximo de reinicios (-1 = ilimitado)
\      actor-id      — id del actor a supervisar
\      watchdog-id   — id del watchdog (usa actor-kill para detenerlo)
\
\  ── Helpers ───────────────────────────────────────────────────────────
\    watch-forever ( interval-ms actor-id -- watchdog-id )
\      Supervisa con reinicios ilimitados
\
\    watch-limited ( interval-ms max actor-id -- watchdog-id )
\      Alias directo de actor-watchdog
\
\    watchdog-stop ( watchdog-id -- )
\      Alias de actor-kill para detener el watchdog
\
\  ── Ejemplo ──────────────────────────────────────────────────────────
\    s" actor-log" load
\    actor-log-start drop
\
\    s" actor-watchdog" load
\
\    : fragile-worker
\      s" worker arrancado" log-info
\      0 begin
\        receive dup -1 = if drop exit then
\        1 + dup . cr
\        dup 3 > if
\          s" worker alcanzó límite y termina" log-warn
\          exit
\        then
\      again ;
\
\    s" fragile-worker" spawn-run value wrk
\    500 ms -1 wrk actor-watchdog value wdg  ( vigilar para siempre )
\    1 wrk actor-send
\    2 wrk actor-send
\    5 wrk actor-send   ( pasará de 3, el actor terminará y watchdog reiniciará )
\    2000 ms 0 do 100 ms 1 do loop loop  ( esperar ~2s observando reinicios )
\    wdg actor-kill
\    wrk actor-kill
\ ════════════════════════════════════════════════════════════════════════

\ watch-forever: supervisa con reinicios ilimitados
: watch-forever ( interval-ms actor-id -- watchdog-id )
  -1 swap   ( interval-ms -1 actor-id )
  actor-watchdog ;

\ watch-limited: alias explícito
: watch-limited ( interval-ms max actor-id -- watchdog-id )
  actor-watchdog ;

\ watchdog-stop: alias legible
: watchdog-stop ( watchdog-id -- )
  actor-kill ;

." Módulo ACTOR-WATCHDOG cargado" cr
." Palabras: actor-watchdog  watch-forever  watch-limited  watchdog-stop" cr
." Uso: 500 ms -1 mi-actor actor-watchdog value wdg" cr
