\ ════════════════════════════════════════════════════════════════
\  Librería PID — control/pid.fth
\  Control Proporcional-Integral-Derivativo en Forth puro
\  Sin interoperabilidad Python.
\
\  Uso básico:
\    s" control/pid" load
\    pid-alloc  variable mi-pid   mi-pid @ pid-init
\    2.0 0.5 0.1  mi-pid @ pid-gains!
\    75.0         mi-pid @ pid-setpoint!
\    0.0 100.0    mi-pid @ pid-limits!
\    0.1          mi-pid @ pid-dt!
\    temperatura-actual  mi-pid @ pid-update  ( -- salida )
\
\  Múltiples instancias independientes:
\    pid-alloc variable pid-temp
\    pid-alloc variable pid-presion
\    pid-alloc variable pid-caudal
\ ════════════════════════════════════════════════════════════════

\ ── Layout de un bloque PID (11 celdas) ─────────────────────────
\  +0  kp          ganancia proporcional
\  +1  ki          ganancia integral
\  +2  kd          ganancia derivativa
\  +3  sp          setpoint (valor objetivo)
\  +4  integral    acumulador integral
\  +5  prev-err    error en la iteración anterior
\  +6  out-min     límite inferior de la salida
\  +7  out-max     límite superior de la salida
\  +8  dt          tiempo de muestreo en segundos
\  +9  last-out    última salida calculada
\  +10 last-err    último error calculado

11 constant pid-size    \ celdas por instancia

\ ── Variables temporales para pid-update ────────────────────────
\  Se usan internamente; no son reentrantes (suficiente para un
\  sistema de control monothread).

variable _pid-err      \ error actual
variable _pid-integ    \ integrador tentativo (antes de anti-windup)
variable _pid-raw      \ salida PID antes de saturar

\ ── Getters ─────────────────────────────────────────────────────

: pid-kp@        ( addr -- val )   @ ;
: pid-ki@        ( addr -- val )  1 + @ ;
: pid-kd@        ( addr -- val )  2 + @ ;
: pid-sp@        ( addr -- val )  3 + @ ;
: pid-integral@  ( addr -- val )  4 + @ ;
: pid-prev-err@  ( addr -- val )  5 + @ ;
: pid-out-min@   ( addr -- val )  6 + @ ;
: pid-out-max@   ( addr -- val )  7 + @ ;
: pid-dt@        ( addr -- val )  8 + @ ;
: pid-output@    ( addr -- val )  9 + @ ;
: pid-error@     ( addr -- val ) 10 + @ ;

\ ── Setters ─────────────────────────────────────────────────────

: pid-kp!        ( val addr -- )   ! ;
: pid-ki!        ( val addr -- )  1 + ! ;
: pid-kd!        ( val addr -- )  2 + ! ;
: pid-sp!        ( val addr -- )  3 + ! ;
: pid-integral!  ( val addr -- )  4 + ! ;
: pid-prev-err!  ( val addr -- )  5 + ! ;
: pid-out-min!   ( val addr -- )  6 + ! ;
: pid-out-max!   ( val addr -- )  7 + ! ;
: pid-dt!        ( val addr -- )  8 + ! ;
: pid-output!    ( val addr -- )  9 + ! ;
: pid-error!     ( val addr -- ) 10 + ! ;

\ ════════════════════════════════════════════════════════════════
\  API pública
\ ════════════════════════════════════════════════════════════════

\ Reserva un bloque PID en la memoria de pfforth.
\ Devuelve la dirección base. Llamar pid-init a continuación.
: pid-alloc  ( -- addr )
  here  pid-size allot
;

\ Inicializa todos los campos.
\ Ganancias = 0.0, límites = ±1e9, dt = 0.1 s.
: pid-init  ( addr -- )
  { pid }
  0.0  pid pid-kp!
  0.0  pid pid-ki!
  0.0  pid pid-kd!
  0.0  pid pid-sp!
  0.0  pid pid-integral!
  0.0  pid pid-prev-err!
  -1e9 pid pid-out-min!
  1e9  pid pid-out-max!
  0.1  pid pid-dt!
  0.0  pid pid-output!
  0.0  pid pid-error!
;

\ Configura las tres ganancias. Orden en pila: Kp Ki Kd addr
: pid-gains!  ( Kp Ki Kd addr -- )
  { pid }
  pid pid-kd!
  pid pid-ki!
  pid pid-kp!
;

\ Fija el valor objetivo (setpoint).
: pid-setpoint!  ( sp addr -- )
  pid-sp!
;

\ Fija los límites de saturación de la salida. Orden: min max addr
: pid-limits!  ( min max addr -- )
  { pid }
  pid pid-out-max!
  pid pid-out-min!
;

\ Resetea el integrador y el estado derivativo.
\ Usar al arrancar o tras un cambio brusco de setpoint.
: pid-reset  ( addr -- )
  { pid }
  0.0 pid pid-integral!
  0.0 pid pid-prev-err!
  0.0 pid pid-output!
  0.0 pid pid-error!
;

\ Calcula una iteración del PID.
\ Entrada: valor medido de la variable física y dirección de la instancia.
\ Salida:  señal de control (dentro de los límites configurados).
\
\ Incluye:
\   - Proporcional:  P = Kp * error
\   - Integral:      I = Ki * suma(error * dt)   con anti-windup
\   - Derivativo:    D = Kd * d(error)/dt
\   - Saturación entre out-min y out-max
\
\ Nota: usa _pid-err, _pid-integ, _pid-raw como temporales.
: pid-update  ( medida addr -- salida )
  { medida pid }

  \ Error = setpoint - medida
  pid pid-sp@ medida -  dup _pid-err !  pid pid-error!

  \ P: término proporcional
  _pid-err @  pid pid-kp@ *

  \ I tentativo: integral acumulada + err*dt
  pid pid-integral@  _pid-err @  pid pid-dt@ *  +
  dup _pid-integ !
  pid pid-ki@ *  +                    \ pila: P+I

  \ D: derivativo = d(error)/dt
  _pid-err @  pid pid-prev-err@ -  pid pid-dt@ /  pid pid-kd@ *  +
                                      \ pila: P+I+D = raw

  \ Guardar error previo para la siguiente llamada
  _pid-err @  pid pid-prev-err!

  \ Guardar raw y saturar la salida
  dup _pid-raw !
  pid pid-out-max@ min  pid pid-out-min@ max   \ pila: salida

  dup pid pid-output!

  \ Anti-windup: aplicar integrador solo si la salida no satura
  _pid-raw @  pid pid-out-max@ <
  _pid-raw @  pid pid-out-min@ > and
  if   _pid-integ @
  else pid pid-integral@
  then
  pid pid-integral!

  \ salida queda en la pila
;
