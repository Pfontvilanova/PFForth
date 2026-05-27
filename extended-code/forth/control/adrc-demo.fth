\ ════════════════════════════════════════════════════════════════
\  Demo ADRC — control/adrc-demo.fth
\  Mismo horno de primer orden que pid-demo.fth
\
\  Planta:  T(k+1) = T(k) + dt * (ctrl - T) / tau
\    tau = 10 s,  dt = 0.1 s
\    T inicial = 20 C,  control ∈ [0, 100 %]
\
\  Parámetros ADRC:
\    b0 = 1/tau = 0.1   (ganancia de entrada de la planta)
\    wc = 1.5 rad/s     (banda del controlador)
\    wo = 8.0 rad/s     (banda del ESO, ~5x wc)
\
\  Carga:
\    s" control/adrc" load
\    s" control/adrc-demo" load
\    demo-adrc
\
\  Pasos   0-149: setpoint 75 C, temperatura inicial 20 C
\  Pasos 150-249: setpoint cambia a 50 C
\ ════════════════════════════════════════════════════════════════

0.1  constant _a-dt
10.0 constant _a-tau

variable _a-temp       \ temperatura actual de la planta
variable _a-ctrl-var   \ instancia ADRC

\ Un paso de la planta simulada.
\ T_new = T + dt * (ctrl - T) / tau
: _a-planta-paso  ( ctrl -- )
  { ctrl }
  _a-temp @
  dup  ctrl swap -  _a-tau /  _a-dt *  +
  _a-temp !
;

\ Inicializar planta y controlador.
: _a-demo-init  ( -- )
  adrc-alloc _a-ctrl-var !
  _a-dt  0.1  1.5  8.0  _a-ctrl-var @ adrc-init
  75.0  _a-ctrl-var @ adrc-setpoint!
  0.0  100.0  _a-ctrl-var @ adrc-limits!
  _a-ctrl-var @ adrc-reset
  20.0  _a-temp !
;

\ Cabecera de la tabla.
: _a-demo-cabecera  ( -- )
  cr
  ." ═══════════════════════════════════════════════════════" cr
  ."  Demo ADRC — Horno de primer orden simulado" cr
  ."  T(k+1) = T(k) + dt*(ctrl-T)/tau    tau=10s  dt=0.1s" cr
  ."  b0=0.1  wc=1.5  wo=8.0    Salida: 0-100 %" cr
  ." ═══════════════════════════════════════════════════════" cr
  cr
  ."  Paso   SP(C)    T(C)   z1-est   Salida(%)" cr
  ."  ─────────────────────────────────────────" cr
;

\ Imprime una fila de la tabla.
: _a-demo-fila  ( paso -- )
  { paso }
  ."  " paso 4 .r
  ."   " _a-ctrl-var @ adrc-sp@  6 .r
  ."   " _a-temp @               6 .r
  ."   " _a-ctrl-var @ adrc-z1@  6 .r
  ."   " _a-ctrl-var @ _adrc-u @ 7 .r
  cr
;

\ Un paso de simulación.
: _a-demo-paso  ( paso -- )
  { paso }
  paso 150 = if
    50.0  _a-ctrl-var @ adrc-setpoint!
    cr ."  >>> Setpoint cambia a 50 C en el paso 150 <<<" cr cr
  then
  _a-temp @  _a-ctrl-var @  adrc-step  _a-planta-paso
  paso 5 mod 0= if  paso _a-demo-fila  then
;

\ Palabra principal.
: demo-adrc  ( -- )
  _a-demo-init
  _a-demo-cabecera
  250 0 do  i _a-demo-paso  loop
  cr ."  Demo completada." cr
;
