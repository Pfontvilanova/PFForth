\ ============================================================
\ actor-camara.fth  —  Actor de camara con deteccion de personas
\ ============================================================
\
\ REQUISITO: cargar el vocabulario de camara primero:
\   IMPORT code/camera
\
\ USO BASICO (camara local):
\   0 ' camara-body actor-spawn  constant mi-cam
\   0 mi-cam actor-send          \ abre camara 0
\
\ USO CON CAMARA IP / ESP32-CAM:
\   s" http://192.168.1.100:81/stream" ' camara-body actor-spawn  constant mi-cam
\   s" http://192.168.1.100:81/stream" mi-cam actor-send
\
\ USO CON ARCHIVO DE VIDEO:
\   s" grabacion.mp4" ' camara-body actor-spawn  constant mi-cam
\   s" grabacion.mp4" mi-cam actor-send
\
\ PARA CON ALARMA:
\   -1 mi-cam actor-send         \ envia señal de stop
\ ============================================================

\ ------------------------------------------------------------
\ Variables globales del actor de camara
\ ------------------------------------------------------------
variable __cam-actor     \ id del actor de camara
variable __cam-alarma    \ id del actor de alarma (0 = ninguno)
variable __cam-min-area  \ area minima de blob para cam-motion?
variable __cam-exterior  \ flag: 1 = camara exterior (usa MOG2), 0 = interior

500  __cam-min-area !
0    __cam-alarma    !
0    __cam-exterior  !

\ ------------------------------------------------------------
\ Palabra auxiliar: envia alarma si hay actor de alarma registrado
\ ------------------------------------------------------------
: cam-alarma-send ( ms -- )
  __cam-alarma @ dup 0> if
    swap actor-send           \ envia timestamp ms al actor alarma
  else
    drop drop                 \ descarta ms y id
  then ;

\ ------------------------------------------------------------
\ Bucle de deteccion para camara INTERIOR
\ (sin filtro MOG2 — el encuadre interior es estable)
\ ------------------------------------------------------------
: camara-interior-loop ( -- )
  begin
    cam-read drop             \ lee frame → imagen activa
    cam-show                  \ muestra en ventana
    cam-person? if            \ YOLO: ¿hay persona?
      cam-pos cam-alarma-send \ avisa con timestamp
    then
    1 ms
    receive-timeout           \ acepta mensajes de control
    over -1 = if              \ si llega -1 → stop
      2drop
      cam-window-close
      cam-close
      exit
    then
    2drop
  again ;

\ ------------------------------------------------------------
\ Bucle de deteccion para camara EXTERIOR
\ (pre-filtro MOG2 para ignorar viento / luces / arboles)
\ ------------------------------------------------------------
: camara-exterior-loop ( -- )
  cam-bg-init                 \ inicializa modelo de fondo adaptativo
  begin
    cam-read drop
    cam-show
    __cam-min-area @ cam-motion? if   \ nivel 1: ¿algo se mueve? (barato)
      cam-person? if                  \ nivel 2: ¿es una persona? (YOLO)
        cam-pos cam-alarma-send
      then
    then
    1 ms
    receive-timeout
    over -1 = if
      2drop
      cam-window-close
      cam-close
      exit
    then
    2drop
  again ;

\ ------------------------------------------------------------
\ Cuerpo principal del actor de camara
\ Recibe la fuente como primer mensaje (entero o string)
\ ------------------------------------------------------------
: camara-body ( -- )
  receive                     \ ( valor actor-origen )
  drop                        \ descarta actor-origen
  cam-open                    \ abre la fuente recibida
  __cam-exterior @ if
    camara-exterior-loop
  else
    camara-interior-loop
  then ;

\ ------------------------------------------------------------
\ Palabras de conveniencia para arrancar y parar
\ ------------------------------------------------------------

\ Arranca el actor con camara local 0
: camara-start ( -- )
  ' camara-body actor-spawn  __cam-actor !
  0 __cam-actor @ actor-send
  ." Actor de camara iniciado (id=" __cam-actor @ . ." )" cr ;

\ Arranca con una URL (deja la URL en pila antes de llamar)
\ Uso: s" http://ip:81/stream" camara-start-url
: camara-start-url ( url -- )
  ' camara-body actor-spawn  __cam-actor !
  __cam-actor @ actor-send
  ." Actor de camara iniciado (id=" __cam-actor @ . ." )" cr ;

\ Para el actor de camara
: camara-stop ( -- )
  __cam-actor @ dup 0> if
    -1 swap actor-send
    __cam-actor @ actor-wait
    0 __cam-actor !
    ." Actor de camara detenido" cr
  else
    drop ." (ningun actor de camara activo)" cr
  then ;

\ Registra el actor de alarma que recibira el timestamp cuando se detecte una persona
\ Uso: mi-actor-alarma camara-alarma!
: camara-alarma! ( actor-id -- )
  __cam-alarma !
  ." Actor de alarma registrado: " __cam-alarma @ . cr ;

\ Activa modo exterior (MOG2) antes de camara-start
: camara-exterior ( -- )
  1 __cam-exterior !
  ." Modo: camara EXTERIOR (filtro MOG2 activo)" cr ;

\ Activa modo interior (sin MOG2) — es el modo por defecto
: camara-interior ( -- )
  0 __cam-exterior !
  ." Modo: camara INTERIOR" cr ;

\ Ajusta el area minima de blob (px^2) para cam-motion? en modo exterior
\ Uso: 800 camara-area!
: camara-area! ( px2 -- )
  __cam-min-area !
  ." Area minima de deteccion: " __cam-min-area @ . ." px^2" cr ;

\ ============================================================
\ EJEMPLOS DE USO
\ ============================================================
\
\ --- Camara interior local ---
\   camara-interior
\   camara-start
\   camara-stop
\
\ --- Camara exterior con zona ROI ---
\   camara-exterior
\   800 camara-area!
\   camara-start
\   10 20 620 460 cam-zone!    \ ignora bordes con arboles
\   camara-stop
\
\ --- ESP32-CAM en exterior ---
\   camara-exterior
\   s" http://192.168.1.100:81/stream" camara-start-url
\   camara-stop
\
\ --- Video grabado con registro de timestamps ---
\   camara-interior
\   ' mi-actor-alarma camara-alarma!
\   s" grabacion.mp4" camara-start-url
\   camara-stop
\ ============================================================
