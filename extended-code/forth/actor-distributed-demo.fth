\ ════════════════════════════════════════════════════════════════════
\  Demo: Sistema distribuido multi-micro con Actor Model (Fase 3)
\  Uso: s" actor-distributed-demo" load
\       demo-local           ( prueba local sin hardware )
\       demo-rutas           ( muestra cómo configurar rutas reales )
\
\  Escenario de producción:
\    ┌────────────────┐  WiFi MQTT    ┌──────────────────┐
\    │  Mac / iPad    │ ◄────────────► │  Raspberry Pi    │
\    │  (REPL)        │               │  (sensor/data)   │
\    └───────┬────────┘               └──────────────────┘
\            │ UART
\    ┌───────▼────────┐
\    │  ESP32         │
\    │  (display)     │
\    └────────────────┘
\
\  Transparencia de ubicación:
\    El código del actor NO cambia si el destino es local o remoto.
\    Solo cambia la configuración de rutas en el arranque de cada nodo.
\
\ ════════════════════════════════════════════════════════════════════════

s" actors"           load
s" actor-transport"  load

\ ── Actores de aplicación ─────────────────────────────────────────────
\
\  Estos actores son idénticos en producción y en la demo local.
\  El id del actor destino se pasa como mensaje inicial para desacoplar
\  la lógica del actor de la configuración de rutas.

\ sensor-loop: genera lecturas simuladas y las envía al display-id
\ Stack durante el bucle: ( acc disp-id )
\   acc     — contador que crece en 1 cada ciclo
\   disp-id — id del actor display (no cambia)
: sensor-loop ( -- )
  receive                  \ primer mensaje: id del display destino
  dup 0 = if drop exit then
  0 swap                   \ ( acc=0 disp-id )
  begin
    swap 1 + swap          \ ( acc+1 disp-id ) — incrementa el contador
    over . cr              \ imprime acc (segundo desde arriba)
    over over actor-send   \ envía acc al display; stack queda ( acc disp-id )
    500 ms receive-timeout \ ( acc disp-id value found )
    drop                   \ ( acc disp-id value ) — descarta found
    -1 = if                \ si value = -1 → señal de parada
      drop drop exit       \ limpia stack y sale
    then
  again ;

\ display-loop: recibe valores y los "muestra"
: display-loop ( -- )
  begin
    receive
    dup -1 = if drop exit then
    ." [DISPLAY] " . cr
  again ;

\ coordinator-loop: arranca el sensor, supervisa, y para todo tras N ciclos
\ Recibe dos mensajes: sensor-id y display-id (en ese orden)
\ Traza de pila:
\   receive receive  →  ( sensor-id display-id )
\   2dup swap actor-send  →  envía display-id al sensor; stack: ( sensor-id display-id )
\   drop  →  ( sensor-id )   guardamos sensor-id para el stop
: coordinator-loop ( -- )
  receive    \ ( sensor-id )
  receive    \ ( sensor-id display-id )
  2dup swap actor-send   \ envía display-id al sensor; stack: ( sensor-id display-id )
  drop                   \ ( sensor-id )
  \ Esperar ~7.5 s (5 × 1500 ms) mientras el sensor trabaja
  5 0 do
    1500 ms receive-timeout 2drop  \ descarta value y found (ambos items)
  loop
  ." coordinator: enviando señal de parada" cr
  -1 swap actor-send     \ envía -1 al sensor; stack: ()
;

\ ── Variables para ids de actores en demo-local ───────────────────────
\ Se declaran aquí para que demo-local pueda referenciarlas por nombre.
variable __disp   0 __disp !
variable __sens   0 __sens !
variable __coord  0 __coord !

\ ── Demo local (sin hardware) ─────────────────────────────────────────
\
\  Crea sensor, display y coordinator en el mismo proceso.
\  La comunicación se hace por colas locales — el código del actor
\  es IDÉNTICO al que correría en el sistema distribuido real.
\  La única diferencia es que en producción se usan rutas remotas.

: demo-local ( -- )
  ." ════ Demo distribuido LOCAL (sin hardware) ════" cr
  ." Actores: sensor, display, coordinator" cr
  ." (mismo código que en producción — sin rutas remotas)" cr cr

  \ Crear actores y guardar sus ids en variables
  s" display-loop"     actor-spawn __disp !
  s" sensor-loop"      actor-spawn __sens !
  s" coordinator-loop" actor-spawn __coord !

  ." actor-ids: sensor=" __sens @ . ." display=" __disp @ . ." coord=" __coord @ . cr

  \ Iniciar todos
  actor-run

  \ Enviar configuración al coordinator (ids de sensor y display)
  __sens @ __coord @ actor-send    \ coordinator ← sensor-id
  __disp @ __coord @ actor-send    \ coordinator ← display-id

  \ Esperar a que el coordinator termine (él envía -1 al sensor antes de salir)
  __coord @ actor-wait

  \ Esperar a que el sensor procese la señal de parada y termine
  __sens @ actor-wait

  ." ════ Deteniendo display ════" cr
  -1 __disp @ actor-send
  __disp @ actor-wait

  ." Demo local completada" cr cr
  ." — Tabla de rutas (vacía en demo local) —" cr
  rutas cr
  ." — Actores registrados —" cr
  actor-list ;

\ ── Configuración de rutas (solo en producción) ───────────────────────
\
\  Estas palabras muestran cómo se configuran las rutas en cada nodo.
\  En la demo local NO se ejecutan (no hay hardware ni red real).

\ arranque-mac: configura el nodo Mac / iPad
\
\  : arranque-mac ( sensor-id-en-rpi display-id-en-esp -- )
\    2dup          ( sens disp sens disp )
\    nip           ( sens disp disp )
\    drop          ( sensor-id-en-rpi )
\    \ NTP para timestamps consistentes (resync cada 5 min)
\    300000 actor-ntp drop
\    \ Recibir mensajes de la RPi por MQTT
\    s" broker.local" 1883 s" pfforth/mac/in" actor-wifi-in drop
\    \ Ruta WiFi al sensor en la RPi
\    swap s" 192.168.1.10" s" pfforth/rpi/in" wifi-canal   ( disp )
\    \ Ruta UART al display en el ESP32
\    swap s" /dev/tty.usbmodem1" uart-115200
\    ." Nodo Mac configurado — rutas activas:" cr rutas ;

\ arranque-rpi: configura el nodo Raspberry Pi
\
\  : arranque-rpi ( mac-coordinator-actor-id -- )
\    300000 actor-ntp drop   \ resync NTP cada 5 minutos
\    \ Escuchar mensajes entrantes del Mac por MQTT
\    s" broker.local" 1883 s" pfforth/rpi/in" actor-wifi-in drop
\    \ Ruta MQTT de vuelta al Mac (coordinator)
\    s" 192.168.1.5" s" pfforth/mac/in" wifi-canal
\    \ Arrancar sensor local
\    s" sensor-loop" spawn-run ;

\ arranque-esp32: configura el ESP32 (MicroPython con pfforth)
\
\  : arranque-esp32 ( -- )
\    \ Escuchar mensajes por UART desde la RPi
\    s" /dev/tty0" 115200 actor-uart-in drop
\    \ Arrancar display local
\    s" display-loop" spawn-run drop ;

\ demo-rutas: muestra la tabla de rutas que tendría el nodo Mac
\  en producción (sin iniciar transportes reales)
: demo-rutas ( -- )
  ." ════ Configuración de rutas en nodo Mac (simulada) ════" cr
  ." (Los actores de transporte no se inician sin hardware real)" cr cr
  ." Ruta WiFi al sensor (actor 10) en RPi 192.168.1.10:" cr
  ." → wifi-ruta-add inicia actor-wifi-out + registrar-ruta" cr
  ." Ruta UART al display (actor 20) en ESP32 /dev/tty.usbmodem1:" cr
  ." → uart-ruta-add inicia actor-uart-out + registrar-ruta" cr cr
  ." Para ejecutar con hardware real, descomenta las palabras" cr
  ." arranque-mac, arranque-rpi y arranque-esp32 al final del fichero." cr ;

." Módulo ACTOR-DISTRIBUTED-DEMO cargado" cr
." Para la demo local sin hardware: demo-local" cr
." Para ver configuración de rutas: demo-rutas" cr
." Para producción: descomenta arranque-mac / arranque-rpi / arranque-esp32" cr
