\ ════════════════════════════════════════════════════════════════
\  Librería ADRC Lineal (LADRC) de 1er orden — control/adrc.fth
\  Active Disturbance Rejection Control
\
\  Arquitectura de tres bloques:
\    TD  — suaviza la referencia (seguidor de primer orden)
\    ESO — Extended State Observer: estima salida y perturbación
\    Ley — u = (u0 - z2) / b0,  u0 = Kp*(v1 - z1)
\
\  Solo hay que ajustar wc (banda del controlador) y wo (banda del
\  ESO, normalmente 3-10 × wc). La perturbación total —dinámicas
\  no modeladas, rozamiento, ruido externo— se estima y cancela.
\
\  Uso básico:
\    s" control/adrc" load
\    adrc-alloc  variable mi-adrc
\    0.1  0.1  1.5  8.0  mi-adrc @ adrc-init  \ h b0 wc wo addr
\    75.0  mi-adrc @  adrc-setpoint!
\    0.0  100.0  mi-adrc @  adrc-limits!
\    mi-adrc @  adrc-reset
\    \ bucle:
\    sensor-leer  mi-adrc @  adrc-step  ( -- u )
\ ════════════════════════════════════════════════════════════════

\ ── Layout del bloque ADRC (13 celdas) ──────────────────────────
\  +0  h         paso de muestreo dt [s]
\  +1  b0        ganancia de entrada de la planta
\  +2  wc        ancho de banda del controlador [rad/s]
\  +3  wo        ancho de banda del ESO [rad/s]
\  +4  z1        ESO — estimación de la salida y
\  +5  z2        ESO — estimación de la perturbación total
\  +6  v1        TD  — referencia suavizada
\  +7  kp        ganancia derivada: kp = wc
\  +8  beta1     ganancia ESO:      beta1 = 2*wo
\  +9  beta2     ganancia ESO:      beta2 = wo^2
\  +10 out-min   límite inferior de la señal de control
\  +11 out-max   límite superior de la señal de control
\  +12 sp        setpoint almacenado

13 constant adrc-size

\ ── Variables temporales para cálculos internos ─────────────────
\  No reentrantes — suficiente para un lazo de control monothread.

variable _adrc-e       \ error del observador: e = y - z1
variable _adrc-u       \ señal de control calculada

\ ── Getters ─────────────────────────────────────────────────────

: adrc-h@       ( addr -- val )   @ ;
: adrc-b0@      ( addr -- val )  1 + @ ;
: adrc-wc@      ( addr -- val )  2 + @ ;
: adrc-wo@      ( addr -- val )  3 + @ ;
: adrc-z1@      ( addr -- val )  4 + @ ;
: adrc-z2@      ( addr -- val )  5 + @ ;
: adrc-v1@      ( addr -- val )  6 + @ ;
: adrc-kp@      ( addr -- val )  7 + @ ;
: adrc-beta1@   ( addr -- val )  8 + @ ;
: adrc-beta2@   ( addr -- val )  9 + @ ;
: adrc-out-min@ ( addr -- val ) 10 + @ ;
: adrc-out-max@ ( addr -- val ) 11 + @ ;
: adrc-sp@      ( addr -- val ) 12 + @ ;

\ ── Setters ─────────────────────────────────────────────────────

: adrc-h!       ( val addr -- )   ! ;
: adrc-b0!      ( val addr -- )  1 + ! ;
: adrc-wc!      ( val addr -- )  2 + ! ;
: adrc-wo!      ( val addr -- )  3 + ! ;
: adrc-z1!      ( val addr -- )  4 + ! ;
: adrc-z2!      ( val addr -- )  5 + ! ;
: adrc-v1!      ( val addr -- )  6 + ! ;
: adrc-kp!      ( val addr -- )  7 + ! ;
: adrc-beta1!   ( val addr -- )  8 + ! ;
: adrc-beta2!   ( val addr -- )  9 + ! ;
: adrc-out-min! ( val addr -- ) 10 + ! ;
: adrc-out-max! ( val addr -- ) 11 + ! ;
: adrc-sp!      ( val addr -- ) 12 + ! ;

\ ════════════════════════════════════════════════════════════════
\  API pública
\ ════════════════════════════════════════════════════════════════

\ Reserva un bloque ADRC en la memoria de pfforth.
: adrc-alloc  ( -- addr )
  here  adrc-size allot
;

\ Inicialización completa: guarda parámetros y calcula ganancias.
\ Orden en pila:  h b0 wc wo addr
\   h   — paso de muestreo [s]
\   b0  — ganancia de entrada de la planta (≈ 1/tau)
\   wc  — banda del controlador [rad/s]  (ej. 1.0 - 5.0)
\   wo  — banda del ESO [rad/s]          (ej. 3*wc - 10*wc)
: adrc-init  ( h b0 wc wo addr -- )
  { ctrl }
  ctrl adrc-wo!
  ctrl adrc-wc!
  ctrl adrc-b0!
  ctrl adrc-h!

  \ Estados iniciales a cero
  0.0  ctrl adrc-z1!
  0.0  ctrl adrc-z2!
  0.0  ctrl adrc-v1!

  \ Límites por defecto
  -1e9 ctrl adrc-out-min!
  1e9  ctrl adrc-out-max!

  \ Setpoint por defecto
  0.0  ctrl adrc-sp!

  \ Ganancias derivadas
  ctrl adrc-wc@                ctrl adrc-kp!      \ kp = wc
  2.0  ctrl adrc-wo@ *         ctrl adrc-beta1!   \ beta1 = 2*wo
  ctrl adrc-wo@  dup  *        ctrl adrc-beta2!   \ beta2 = wo^2
;

\ Fija el valor objetivo.
: adrc-setpoint!  ( sp addr -- )
  adrc-sp!
;

\ Fija los límites de la señal de control. Orden: min max addr
: adrc-limits!  ( min max addr -- )
  { ctrl }
  ctrl adrc-out-max!
  ctrl adrc-out-min!
;

\ Reinicia los estados del ESO y del TD sin tocar los parámetros.
: adrc-reset  ( addr -- )
  { ctrl }
  0.0  ctrl adrc-z1!
  0.0  ctrl adrc-z2!
  0.0  ctrl adrc-v1!
;

\ ── Bloque interno: Generador de Trayectorias (TD) ──────────────
\  Filtro de primer orden sobre la referencia.
\  v1_nueva = v1 + h * wc * (sp - v1)
\  Devuelve v1_nueva en la pila y actualiza el campo.
: _adrc-td  ( addr -- v1_nueva )
  { ctrl }
  ctrl adrc-sp@  ctrl adrc-v1@  -     \ sp - v1
  ctrl adrc-wc@  *                    \ wc * (sp - v1)
  ctrl adrc-h@   *                    \ h  * wc * (sp - v1)
  ctrl adrc-v1@  +                    \ v1 + ...
  dup  ctrl adrc-v1!                  \ actualizar v1
;

\ ── Bloque interno: Observer de Estado Extendido (ESO) ──────────
\  Integración Euler:
\    e       = y - z1
\    z1_dot  = z2 + b0*u + beta1*e
\    z2_dot  = beta2 * e
\    z1_new  = z1 + h * z1_dot
\    z2_new  = z2 + h * z2_dot
: _adrc-eso  ( y u addr -- )
  { y u ctrl }

  \ Error del observador
  y  ctrl adrc-z1@  -  _adrc-e !

  \ z1_dot = z2 + b0*u + beta1*e
  ctrl adrc-z2@
  ctrl adrc-b0@  u  *  +
  ctrl adrc-beta1@  _adrc-e @  *  +       \ z1_dot en pila

  \ z1_new = z1 + h * z1_dot
  ctrl adrc-h@  *  ctrl adrc-z1@  +  ctrl adrc-z1!

  \ z2_dot = beta2 * e
  ctrl adrc-beta2@  _adrc-e @  *          \ z2_dot en pila

  \ z2_new = z2 + h * z2_dot
  ctrl adrc-h@  *  ctrl adrc-z2@  +  ctrl adrc-z2!
;

\ ── Palabra principal: un ciclo completo ADRC ───────────────────
\  Recibe la medida actual, devuelve la señal de control.
\
\  Secuencia:
\    1. TD  → v1 (referencia suavizada)
\    2. u0  = Kp * (v1 - z1)
\    3. u   = (u0 - z2) / b0      (cancelación de perturbación)
\    4. Saturar u en [out-min, out-max]
\    5. ESO → actualizar z1, z2 con y y u actuales
: adrc-step  ( y addr -- u )
  { y ctrl }

  \ 1. TD: referencia suavizada
  ctrl _adrc-td                            \ v1 en pila

  \ 2. u0 = Kp * (v1 - z1)
  ctrl adrc-z1@  -                         \ v1 - z1
  ctrl adrc-kp@  *                         \ u0

  \ 3. u = (u0 - z2) / b0
  ctrl adrc-z2@  -                         \ u0 - z2
  ctrl adrc-b0@  /                         \ u (sin saturar)

  \ 4. Saturación
  ctrl adrc-out-max@  min
  ctrl adrc-out-min@  max                  \ u saturada

  \ 5. Actualizar ESO con y y u de este ciclo
  dup  _adrc-u !
  y  _adrc-u @  ctrl  _adrc-eso

  \ u queda en la pila
;
