\ ════════════════════════════════════════════════════════════════════
\  Módulo ACTORS — Actor Model para pfforth (Fase 1 + 2)
\  Uso: s" actors" load
\
\  Las palabras actor son primitivas del intérprete (siempre disponibles).
\  Este fichero define utilidades de alto nivel y ejemplos funcionales.
\
\  ── Creación ──────────────────────────────────────────────────────────
\    actor-spawn   ( xt|name -- actor-id )      Crea actor (pendiente)
\                  Acepta xt de ' word  o  string de s" name"
\    actor-run     ( -- )                      Arranca todos los pendientes
\    actor-kill    ( actor-id -- )             Detiene y elimina un actor
\
\  ── Mensajes ──────────────────────────────────────────────────────────
\    actor-send    ( value actor-id -- )       Envía mensaje a un actor
\    receive       ( -- msg )                  Espera mensaje (bloquea; funciona desde REPL)
\    receive-timeout ( ms -- value found )     Espera con límite; found=-1 OK, 0=vacío
\    broadcast     ( value -- )               Envía a todos los actores vivos
\
\  ── Respuesta al sender ───────────────────────────────────────────────
\    sender-id     ( -- id )                   Id del actor que envió el último msg
\    reply         ( value -- )               Responde al sender del último msg
\
\  ── Consulta ──────────────────────────────────────────────────────────
\    actor-id      ( -- id )                   Id del actor actual (0=REPL)
\    actor-alive?  ( actor-id -- flag )        -1 si vivo, 0 si no
\    actor-list    ( -- )                      Tabla de actores registrados
\    actor-wait    ( actor-id -- )             Espera a que un actor termine
\
\  ── Comportamiento ────────────────────────────────────────────────────
\    reactive      ( actor-id -- )             Modo reactivo (por defecto)
\    proactive     ( interval-ms actor-id -- ) Modo proactivo: tick periódico
\
\  ── Infraestructura (Fase 2) ──────────────────────────────────────────
\    actor-watchdog ( interval-ms max-retries actor-id -- watchdog-id )
\    actor-log-start ( -- log-id )             Inicia logger centralizado
\
\  ── Tiempo ────────────────────────────────────────────────────────────
\    ms            ( n -- n )                  n ya está en ms (legibilidad)
\    s             ( n -- n*1000 )             Segundos a milisegundos
\ ════════════════════════════════════════════════════════════════════════

\ ── Utilidades de alto nivel ──────────────────────────────────────────

\ spawn-run: crea e inicia un actor en una sola línea
\ Uso con tick:   ' mi-palabra spawn-run  ( -- actor-id )
\ Uso con string: s" mi-palabra" spawn-run  ( -- actor-id )
: spawn-run ( xt|name -- actor-id )
  actor-spawn
  dup >r
  actor-run
  r> ;

\ send-to: azúcar para actor-send con orden natural
\ Uso: 42 send-to mi-actor
: send-to ( value actor-id -- )
  actor-send ;

\ alive?: alias legible
: alive? ( actor-id -- flag )
  actor-alive? ;

\ ── Ejemplo 1: Actor contador reactivo ───────────────────────────────
\
\ Recibe números, acumula la suma y la imprime.
\ Enviar -1 lo detiene.
\
\ Uso:
\   s" counter-body" spawn-run value cnt
\   42 cnt actor-send
\   10 cnt actor-send
\   -1 cnt actor-send    ( detiene )

: counter-body ( -- )
  0
  begin
    receive
    dup -1 = if drop drop exit then
    + dup . cr
  again ;

\ ── Ejemplo 2: Actor eco con reply ───────────────────────────────────
\
\ Recibe cualquier valor, lo imprime y responde al sender duplicado.
\
\ Uso:
\   s" echo-body" spawn-run value eco

: echo-body ( -- )
  begin
    receive
    dup 0 = if drop exit then
    dup ." eco: " . cr
    2 * reply
  again ;

\ ── Ejemplo 3: Actor timer proactivo ─────────────────────────────────
\
\ Recibe tick cada N ms e incrementa un contador interno.
\
\ Uso:
\   s" ticker-body" actor-spawn value tmr
\   500 ms tmr proactive     ( tick cada 500 ms )
\   actor-run

: ticker-body ( -- )
  0
  begin
    receive drop
    1 + dup . cr
  again ;

." Módulo ACTORS cargado (Fase 1+2+3)" cr
." Fase 1: actor-spawn actor-run actor-kill actor-send" cr
."         receive receive-timeout actor-id actor-alive?" cr
."         actor-list reactive proactive ms s" cr
." Fase 2: sender-id reply broadcast actor-wait" cr
."         actor-watchdog actor-log-start" cr
." Fase 3: (cargar actor-transport para rutas y transportes)" cr
."         wifi-ruta-add  uart-ruta-add  ruta-del  rutas" cr
."         actor-wifi-in  actor-uart-in" cr
."         actor-ntp  actor-time" cr
." Helpers: spawn-run send-to alive?" cr
." Ejemplos: counter-body  echo-body  ticker-body" cr
