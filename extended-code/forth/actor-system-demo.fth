\ ════════════════════════════════════════════════════════════════════
\  Demo: Sistema multi-actor con logger y watchdog
\  Uso: s" actor-system-demo" load
\
\  Arquitectura del sistema de demostración:
\    - logger     : actor-log centralizado
\    - worker     : actor reactivo que procesa números
\    - monitor    : actor que consulta al worker periódicamente (reply)
\    - watchdog   : supervisa al worker y lo reinicia si falla
\ ════════════════════════════════════════════════════════════════════════

\ ── 1. Cargar módulos necesarios ──────────────────────────────────────
s" actors"         load  ( helpers Fase 1+2 )
s" actor-log"      load  ( logger centralizado )
s" actor-watchdog" load  ( watchdog )

\ ── 2. Iniciar logger ─────────────────────────────────────────────────
actor-log-start drop

s" Sistema demo iniciando..." log-info

\ ── 3. Worker reactivo ────────────────────────────────────────────────
\  Recibe números, los acumula, responde la suma al sender.
\  Termina con -1. Si recibe -99 simula un crash.

variable __worker-sum  0 __worker-sum !

: worker-body ( -- )
  s" worker: listo" log-info
  begin
    receive
    dup -1 = if
      drop
      s" worker: recibió -1, terminando limpiamente" log-info
      exit
    then
    dup -99 = if
      drop
      s" worker: ¡crash simulado!" log-error
      exit    ( termina sin enviar reply )
    then
    __worker-sum @ + dup __worker-sum !
    dup reply   ( responde suma acumulada al sender )
  again ;

\ ── 4. Monitor proactivo ─────────────────────────────────────────────
\  Cada tick envía el contador al worker y espera la suma de respuesta.
\  Stack en cada iteración:
\    receive drop              → ()
\    ...dup __monitor-count !  → ( count )
\    [alive?] if               → ( count )
\      dup actor-send          → ( count )       envía count, queda count
\      receive-timeout         → ( count reply found )
\      if                      → ( count reply )  if pops found
\        . cr                  → ( count )        imprime reply
\      else drop cr            → ( count )        descarta reply=0
\      then                    → ( count )
\    else cr                   → ( count )
\    then                      → ( count )
\    dup 5 > if drop exit then → ()  si count>5 termina

variable __monitor-count  0 __monitor-count !
variable __worker-id      0 __worker-id !

: monitor-body ( -- )
  s" monitor: arrancado" log-info
  begin
    receive drop                                  ( tick )
    __monitor-count @ 1 + dup __monitor-count !   ( count )
    __worker-id @ actor-alive? if
      dup __worker-id @ actor-send                ( count — envía count al worker )
      200 ms receive-timeout                      ( count reply found )
      if                                          ( count reply — found era -1: OK )
        ." monitor < suma=" . cr                  ( count )
      else
        drop                                      ( count — descarta reply=0 )
        ." monitor: timeout esperando worker" cr
      then
    else
      ." monitor: worker no disponible" cr
    then
    dup 10 > if drop exit then
  again ;

\ ── 5. Ensamblar el sistema ───────────────────────────────────────────

." --- Arrancando sistema demo ---" cr

\ Crear actores
\ IMPORTANTE: el monitor se crea DESPUÉS de asignar __worker-id
\ para que el hijo herede ya el id correcto del worker.
s" worker-body"  actor-spawn value __wrk-id
__wrk-id __worker-id !

s" monitor-body" actor-spawn value __mon-id

\ Configurar monitor como proactivo (tick cada 300ms)
300 ms __mon-id proactive

\ Arrancar todos los actores pendientes
actor-run

\ Vigilar el worker con watchdog (intervalo=400ms, max=2 reinicios)
400 ms 2 __wrk-id actor-watchdog value __wdg-id

s" Sistema demo en marcha" log-info

." worker-id="  __wrk-id  . cr
." monitor-id=" __mon-id  . cr
." watchdog-id=" __wdg-id . cr
." " cr
." Prueba: envía -99 al worker para simular crash:" cr
."   -99 __wrk-id actor-send" cr
." Prueba: envía -1 para terminar limpio:" cr
."   -1 __wrk-id actor-send" cr
." Para parar todo:" cr
."   __wdg-id actor-kill  __mon-id actor-kill  __wrk-id actor-kill" cr
