\ ════════════════════════════════════════════════════════════════════
\  Módulo ACTOR-TRANSPORT — Comunicación distribuida multi-micro
\  Uso: s" actor-transport" load
\
\  Extiende el Actor Model (Fase 3) para enrutar mensajes de forma
\  transparente entre micros distintos vía WiFi (MQTT o TCP), UART o SPI.
\  El código del actor NO cambia: actor-send funciona igual si el
\  destino es local o remoto — la tabla de rutas decide cómo enviarlo.
\
\  ── Arquitectura ─────────────────────────────────────────────────────
\
\  actor-send consulta la tabla de rutas antes de entregar:
\    • actor local → cola directa (comportamiento Fase 1)
\    • actor remoto → cola del actor de transporte OUT correspondiente
\
\  Cada transporte OUT es un actor Python registrado en el registry:
\    actor-wifi-out      → publica JSON por MQTT (paho-mqtt)
\    actor-wifi-tcp-out  → envía JSON por TCP (newline-delimitado)
\    actor-uart-out      → escribe tramas binarias por puerto serie (pyserial)
\    actor-spi-out       → escribe tramas binarias por SPI (spidev, Linux)
\
\  Cada transporte IN también es un actor Python registrado:
\    actor-wifi-in       → suscriptor MQTT, entrega localmente
\    actor-wifi-tcp-in   → servidor TCP, entrega localmente
\    actor-uart-in       → lector serie, entrega localmente
\    actor-spi-in        → lector SPI, entrega localmente
\
\  ── Tabla de rutas ───────────────────────────────────────────────────
\
\  Primitiva genérica (bajo nivel):
\    registrar-ruta ( actor-id transport-str transport-actor-id -- )
\      Asocia actor-id con un actor de transporte OUT ya iniciado.
\      transport-str — etiqueta legible ('mqtt', 'tcp', 'uart', 'spi')
\      transport-actor-id — id del actor OUT que maneja el envío
\
\    ruta-buscar ( actor-id -- endpoint-str | 0 )
\      Devuelve una cadena con el endpoint remoto del actor-id, o 0 si local.
\      Ej: "mqtt:192.168.1.10:1883/pfforth/rpi/in  (via actor-3)"
\      Test de existencia: ruta-buscar 0 <> if ... then
\
\    ruta-del  ( actor-id -- )
\      Elimina la ruta de un actor-id (vuelve a ser local).
\
\    rutas     ( -- )
\      Imprime la tabla de rutas actual con detalle de transporte.
\
\  Wrappers de conveniencia (inician transporte + registran ruta):
\    wifi-ruta-add      ( actor-id host port topic -- )
\    uart-ruta-add      ( actor-id device baud -- )
\    spi-ruta-add       ( actor-id device speed -- )
\
\  ── Actores de transporte saliente (OUT) ─────────────────────────────
\
\    actor-wifi-out     ( host port topic -- actor-id )
\      Actor MQTT OUT. Recibe (to-id, value) y publica JSON.
\      Requiere: pip install paho-mqtt
\
\    actor-wifi-tcp-out ( host port -- actor-id )
\      Actor TCP OUT. Envía una línea JSON por conexión TCP.
\
\    actor-uart-out     ( device baud -- actor-id )
\      Actor UART OUT. Escribe tramas binarias en el puerto serie.
\      Requiere: pip install pyserial
\
\    actor-spi-out      ( device speed -- actor-id )
\      Actor SPI OUT. Escribe tramas binarias vía spidev.
\      device = '0.0' para /dev/spidev0.0, speed en Hz.
\      Requiere: pip install spidev  (Linux)
\
\  ── Actores de transporte entrante (IN) ──────────────────────────────
\
\    actor-wifi-in      ( host port topic -- actor-id )
\      Suscriptor MQTT. Entrega mensajes a actores locales.
\
\    actor-wifi-tcp-in  ( port -- actor-id )
\      Servidor TCP. Entrega mensajes JSON (newline-delimitado).
\
\    actor-uart-in      ( device baud -- actor-id )
\      Lector UART. Decodifica tramas y entrega localmente.
\
\    actor-spi-in       ( device speed -- actor-id )
\      Lector SPI. Decodifica tramas y entrega localmente.
\
\  ── Tiempo sincronizado ──────────────────────────────────────────────
\
\    actor-ntp  ( interval-ms -- actor-id )
\      Inicia un actor proactivo que sincroniza con pool.ntp.org.
\      Sincroniza una vez al arrancar y luego cada interval-ms ms.
\      interval-ms = 0 → sincroniza una sola vez y termina.
\      Uso típico: 300000 actor-ntp drop   ( resync cada 5 minutos )
\      Sin red el actor sigue vivo y reintenta en cada intervalo.
\
\    actor-time ( -- ms )
\      Unix-time en milisegundos con ajuste NTP. Usar para correlacionar
\      logs y eventos entre nodos con relojes distintos.
\
\  ── Protocolo de transporte ──────────────────────────────────────────
\
\  WiFi MQTT / TCP: JSON
\    {"proto":"pfforth-actor","v":1,"to":<int>,"from":<int>,"msg":<valor>}
\    TCP: JSON seguido de \n (newline-delimitado)
\
\  UART / SPI: trama binaria
\    [0xAC] [0xE0] [len_hi] [len_lo] [json_bytes…]
\    donde json_bytes es el mismo JSON que en WiFi
\
\ ════════════════════════════════════════════════════════════════════════

\ ── Helpers de alto nivel ─────────────────────────────────────────────

\ wifi-canal: registra ruta WiFi MQTT con puerto estándar 1883
\ Inicia automáticamente un actor-wifi-out si no existe para ese endpoint.
\ Uso: 5 s" 192.168.1.10" s" pfforth/rpi/in" wifi-canal
: wifi-canal ( actor-id host topic -- )
  >r           ( actor-id host )
  1883         ( actor-id host 1883 )
  r>           ( actor-id host 1883 topic )
  wifi-ruta-add ;

\ wifi-canal-ssl: igual pero con puerto 8883
: wifi-canal-ssl ( actor-id host topic -- )
  >r 8883 r> wifi-ruta-add ;

\ tcp-canal: registra ruta WiFi TCP
\ Uso: 5 s" 192.168.1.10" 9000 tcp-canal
: tcp-canal ( actor-id host port -- )
  \ Inicia transport OUT y registra ruta
  2dup actor-wifi-tcp-out   ( actor-id host port tcp-out-id )
  >r                        ( actor-id host port )
  2drop                     ( actor-id )
  s" tcp" r>                ( actor-id s"tcp" tcp-out-id )
  registrar-ruta ;

\ uart-115200: registra ruta UART a 115200 bauds
\ Uso: 3 s" /dev/ttyUSB0" uart-115200
: uart-115200 ( actor-id device -- )
  115200 uart-ruta-add ;

\ spi-500k: registra ruta SPI a 500 kHz
\ Uso: 7 s" 0.0" spi-500k
: spi-500k ( actor-id device -- )
  500000 spi-ruta-add ;

\ ntp-sync: sincroniza una sola vez con NTP
: ntp-sync ( -- )
  0 actor-ntp drop ;

\ ntp-auto: inicia resync automático cada 5 minutos, devuelve actor-id
\ Uso: ntp-auto value ntp-actor   ( para poder matarlo después )
: ntp-auto ( -- actor-id )
  300000 actor-ntp ;

\ es-remoto?: devuelve -1 si actor-id tiene ruta registrada, 0 si local
: es-remoto? ( actor-id -- flag )
  ruta-buscar 0 <> ;

\ ── Ejemplos de uso ───────────────────────────────────────────────────

\ Ejemplo 1: Configurar nodo REPL para hablar con RPi por MQTT
\
\   s" actors" load  s" actor-transport" load
\   0 actor-ntp drop   \ sincroniza una vez al arrancar
\
\   \ Iniciar transporte de entrada (mensajes que llegan de la RPi)
\   s" broker.local" 1883 s" pfforth/mac/in" actor-wifi-in value rx-mac
\
\   \ Registrar ruta para el actor 10 que vive en la RPi
\   10 s" 192.168.1.10" s" pfforth/rpi/in" wifi-canal
\
\   \ Ahora actor-send funciona igual localmente y en remoto:
\   42 10 actor-send    \ → JSON publicado en pfforth/rpi/in
\
\ ─────────────────────────────────────────────────────────────────────

\ Ejemplo 2: Configurar nodo RPi para hablar con ESP32 por UART
\
\   s" actors" load  s" actor-transport" load
\
\   \ Iniciar transporte de entrada por UART
\   s" /dev/ttyUSB1" 115200 actor-uart-in value rx-uart
\
\   \ Registrar ruta para el actor 20 que vive en el ESP32
\   20 s" /dev/ttyUSB0" uart-115200
\
\   \ Enviar lectura al display:
\   99 20 actor-send    \ → trama binaria por UART

\ ─────────────────────────────────────────────────────────────────────

\ Ejemplo 3: Configurar nodo con SPI (RPi ↔ ESP32 hardware SPI)
\
\   s" actors" load  s" actor-transport" load
\
\   s" 0.0" 500000 actor-spi-in drop   \ escuchar en SPI bus0 dev0
\   30 s" 0.0" spi-500k               \ actor-30 en ESP32 vía SPI

\ ─────────────────────────────────────────────────────────────────────

\ Ejemplo 4: registrar-ruta manual (control total)
\
\   \ 1. Iniciar actor de transporte OUT
\   s" broker.local" 1883 s" pfforth/esp32/in" actor-wifi-out value mqtt-esp
\
\   \ 2. Registrar ruta para actor-id 30 usando ese transporte
\   30 s" mqtt" mqtt-esp registrar-ruta
\
\   \ 3. Verificar la ruta
\   30 ruta-buscar . cr    \ → imprime id del mqtt-esp actor
\   30 es-remoto? . cr     \ → -1
\
\   \ 4. actor-send enruta automáticamente
\   hello-msg 30 actor-send

." Módulo ACTOR-TRANSPORT cargado (Fase 3)" cr
." Tabla de rutas: registrar-ruta  ruta-buscar  ruta-del  rutas" cr
." Wrappers:       wifi-ruta-add  uart-ruta-add  spi-ruta-add" cr
." OUT:            actor-wifi-out  actor-wifi-tcp-out" cr
."                 actor-uart-out  actor-spi-out" cr
." IN:             actor-wifi-in  actor-wifi-tcp-in" cr
."                 actor-uart-in  actor-spi-in" cr
." Tiempo NTP:     actor-ntp  actor-time" cr
." Helpers:        wifi-canal  wifi-canal-ssl  tcp-canal" cr
."                 uart-115200  spi-500k  ntp-sync  es-remoto?" cr
