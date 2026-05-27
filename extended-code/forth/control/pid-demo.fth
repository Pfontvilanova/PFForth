\ ════════════════════════════════════════════════════════════════
\  Demo PID — control/pid-demo.fth
\  Simula el calentamiento de un horno controlado por PID
\
\  Carga:
\    s" control/pid" load
\    s" control/pid-demo" load
\    demo-pid
\
\  La demo corre 250 pasos (dt=0.1 s → 25 s reales):
\    Pasos   0-149: setpoint 75 C, temperatura inicial 20 C
\    Pasos 150-249: setpoint cambia a 50 C (perturbación)
\  Se imprime el estado cada 5 pasos.
\ ════════════════════════════════════════════════════════════════

\ ── Parámetros de la planta simulada ────────────────────────────
\  Modelo de primer orden: horno con calefactor eléctrico
\    T(k+1) = T(k) + dt * (ctrl - T) / tau
\    T    = temperatura actual [°C]
\    ctrl = potencia del calefactor [0..100 %]
\    tau  = constante de tiempo del horno [s]
\    dt   = periodo de muestreo [s]

0.1  constant _dt
10.0 constant _tau

variable _temp       \ temperatura actual de la planta
variable _demo-pid   \ dirección de la instancia PID

\ Avanza la planta un paso dado el control aplicado.
\ Usa operaciones de pila para T_new = T + dt*(ctrl-T)/tau
: _planta-paso  ( ctrl -- )
  { ctrl }
  _temp @                     \ pila: T
  dup  ctrl swap -            \ pila: T (ctrl-T)
  _tau /  _dt *               \ pila: T dt*(ctrl-T)/tau
  +  _temp !                  \ _temp = T_new
;

\ ── Inicialización ───────────────────────────────────────────────
: _demo-init  ( -- )
  pid-alloc _demo-pid !
  _demo-pid @ pid-init
  3.0 0.8 0.2  _demo-pid @ pid-gains!
  75.0         _demo-pid @ pid-setpoint!
  0.0 100.0    _demo-pid @ pid-limits!
  _dt          _demo-pid @ pid-dt!
  20.0         _temp !
;

\ ── Cabecera de la tabla ─────────────────────────────────────────
: _demo-cabecera  ( -- )
  cr
  ." ═══════════════════════════════════════════════════════" cr
  ."  Demo PID — Horno de primer orden simulado" cr
  ."  T(k+1) = T(k) + dt*(ctrl-T)/tau    tau=10s  dt=0.1s" cr
  ."  Kp=3.0  Ki=0.8  Kd=0.2    Salida: 0-100 %" cr
  ." ═══════════════════════════════════════════════════════" cr
  cr
  ."  Paso   SP(C)    T(C)    Error   Salida(%)" cr
  ."  ─────────────────────────────────────────" cr
;

\ ── Imprime una fila de la tabla ─────────────────────────────────
: _demo-fila  ( paso -- )
  { paso }
  ."  " paso 4 .r
  ."   " _demo-pid @ pid-sp@     6 .r
  ."   " _temp @                 6 .r
  ."   " _demo-pid @ pid-error@  7 .r
  ."   " _demo-pid @ pid-output@ 7 .r
  cr
;

\ ── Un paso de simulación ────────────────────────────────────────
: _demo-paso  ( paso -- )
  { paso }
  \ Cambio de setpoint en el paso 150
  paso 150 = if
    50.0 _demo-pid @ pid-setpoint!
    cr ."  >>> Setpoint cambia a 50 C en el paso 150 <<<" cr cr
  then
  \ Medir, calcular PID y aplicar a la planta
  _temp @  _demo-pid @ pid-update  _planta-paso
  \ Imprimir cada 5 pasos
  paso 5 mod 0= if  paso _demo-fila  then
;

\ ── Palabra principal ────────────────────────────────────────────
: demo-pid  ( -- )
  _demo-init
  _demo-cabecera
  250 0 do  i _demo-paso  loop
  cr ."  Demo completada." cr
;
