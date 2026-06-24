\ ════════════════════════════════════════════════════════════════
\  Librería de Estructuras — estructuras/estructuras.fth
\  Cálculo simplificado de vigas isostáticas e hiperestáticas
\
\  Unidades del sistema:  mm · N · N/mm² · N·mm
\    Longitud:   mm      (1 m = 1000 mm)
\    Fuerza:     N       (1 kN = 1000 N)
\    Tensión:    N/mm²   (= MPa)
\    Momento:    N·mm
\    Inercia:    mm⁴
\    Carga dist: N/mm    (1 kN/m = 1 N/mm)
\
\  Carga:
\    s" estructuras/estructuras" load
\
\  Uso rápido:
\    acero  ipe200  biapoyada
\    5000.0 L!   0.5 q!        \ L=5 m, q=0.5 kN/m
\    flecha                     \ calcula y muestra la flecha
\    300 flim!                  \ límite L/300
\    inercia                    \ I mínimo para no superar L/300
\
\  Palabras bidireccionales:
\    sin argumento → calcula e imprime
\    con argumento → fija el valor (para cálculo inverso)
\    Ej: flecha        → calcula f con los parámetros actuales
\    Ej: 15.0 flecha   → fija f = 15 mm
\    Ej: inercia       → I mínimo para f fijado
\ ════════════════════════════════════════════════════════════════

\ ── Variables de estado ─────────────────────────────────────────
variable _E           \ módulo elástico [N/mm²]
variable _G           \ módulo cortante [N/mm²]
variable _rho         \ densidad [kg/m³]
variable _fy          \ límite elástico [N/mm²]
variable _i           \ inercia sección [mm⁴]
variable _W           \ módulo resistente [mm³]
variable _l           \ longitud viga [mm]
variable _q           \ carga distribuida [N/mm]
variable _P           \ carga puntual [N]
variable _a           \ posición carga puntual desde apoyo 1 [mm]
variable _M           \ momento exterior aplicado [N·mm]
variable _f           \ flecha calculada o fijada [mm]
variable _fLim        \ límite de flecha [mm]  (ej. L/300)
variable _k1          \ coef. flecha
variable _k2          \ coef. momento
variable _tipoCarga   \ 1=uniforme  2=puntual-centro  3=puntual-pos
variable _tipoApoyo   \ 1=biapoyada  2=empotrada  3=voladizo  4=emp-apoyada
variable _R1          \ reacción apoyo 1 [N]
variable _R2          \ reacción apoyo 2 [N]

\ Inicializar a cero
0.0 _E !  0.0 _G !  0.0 _i !  0.0 _W !
0.0 _l !  0.0 _q !  0.0 _P !  0.0 _a !  0.0 _M !
0.0 _f !  0.0 _fLim !  0.0 _k1 !  0.0 _k2 !
1 _tipoCarga !  1 _tipoApoyo !
0.0 _R1 !  0.0 _R2 !

\ Temporales internos para cálculo de tubos
variable _bi   variable _hi

\ ── Materiales ──────────────────────────────────────────────────

: acero    210000.0 _E !   81000.0 _G !   7850.0 _rho !  355.0 _fy ! ;
: aluminio  70000.0 _E !   26000.0 _G !   2700.0 _rho !  150.0 _fy ! ;
: madera    11000.0 _E !     690.0 _G !    420.0 _rho !   24.0 _fy ! ;
: hormigon  30000.0 _E !   12000.0 _G !   2400.0 _rho !   30.0 _fy ! ;

\ ── Inercia de tubo rectangular hueco ──────────────────────────
\  b=ancho exterior  h=alto exterior  t=espesor de pared  (mm)
\  I = (b·h³ − bi·hi³) / 12    donde bi=b−2t, hi=h−2t
\
\  NOTA: x³ en Forth = x dup dup * *   (x → x x x → x x² → x³)
\        NO usar dup * dup * que da x⁴
: tubo-I  ( b h t -- I_mm4 )
  { b h t }
  b 2.0 t * -  _bi !              \ bi = b − 2t
  h 2.0 t * -  _hi !              \ hi = h − 2t
  b   h dup dup * *  *            \ b × h³
  _bi @  _hi @ dup dup * *  *     \ bi × hi³
  -
  12.0 /
;

\ Atajo: calcula y guarda en _i directamente
: tubo  ( b h t -- )   tubo-I  _i ! ;

\ ── Perfiles IPN — Iy en mm⁴  (EN 10034) ───────────────────────
: ipn100   1710000.0   _i ! ;
: ipn120   3280000.0   _i ! ;
: ipn140   5730000.0   _i ! ;
: ipn160   9350000.0   _i ! ;
: ipn180  14500000.0   _i ! ;
: ipn200  21400000.0   _i ! ;
: ipn220  30600000.0   _i ! ;
: ipn240  42500000.0   _i ! ;
: ipn260  57400000.0   _i ! ;
: ipn280  75900000.0   _i ! ;
: ipn300  98000000.0   _i ! ;
: ipn320 125100000.0   _i ! ;
: ipn340 157000000.0   _i ! ;
: ipn360 196100000.0   _i ! ;
: ipn380 240100000.0   _i ! ;
: ipn400 292100000.0   _i ! ;
: ipn450 458500000.0   _i ! ;
: ipn500 687400000.0   _i ! ;

\ ── Perfiles IPE — Iy en mm⁴  (EN 10365) ───────────────────────
: ipe80    801000.0    _i ! ;
: ipe100  1710000.0    _i ! ;
: ipe120  3180000.0    _i ! ;
: ipe140  5410000.0    _i ! ;
: ipe160  8690000.0    _i ! ;
: ipe180 13170000.0    _i ! ;
: ipe200 19430000.0    _i ! ;
: ipe220 27720000.0    _i ! ;
: ipe240 38920000.0    _i ! ;
: ipe270 57900000.0    _i ! ;
: ipe300 83560000.0    _i ! ;
: ipe330 117700000.0   _i ! ;
: ipe360 162700000.0   _i ! ;
: ipe400 231300000.0   _i ! ;
: ipe450 337400000.0   _i ! ;
: ipe500 482000000.0   _i ! ;
: ipe550 671200000.0   _i ! ;
: ipe600 920800000.0   _i ! ;

\ ── Perfiles HEB — Iy en mm⁴  (EN 10365) ───────────────────────
: heb100   4495000.0   _i ! ;
: heb120   8640000.0   _i ! ;
: heb140  15090000.0   _i ! ;
: heb160  24920000.0   _i ! ;
: heb180  38310000.0   _i ! ;
: heb200  56960000.0   _i ! ;
: heb220  80910000.0   _i ! ;
: heb240 112600000.0   _i ! ;
: heb260 149200000.0   _i ! ;
: heb280 192700000.0   _i ! ;
: heb300 251700000.0   _i ! ;
: heb320 308200000.0   _i ! ;
: heb340 366600000.0   _i ! ;
: heb360 431900000.0   _i ! ;
: heb400 576800000.0   _i ! ;
: heb450 798900000.0   _i ! ;
: heb500 1072000000.0  _i ! ;
: heb550 1367000000.0  _i ! ;
: heb600 1710000000.0  _i ! ;

\ ════════════════════════════════════════════════════════════════
\  Configuraciones (condición de apoyo + tipo de carga)
\
\  Fórmulas aplicadas:
\    f = k1 × q × L⁴ / (E × I)    carga distribuida
\    f = k1 × P × L³ / (E × I)    carga puntual
\    M = k2 × q × L²              carga distribuida
\    M = k2 × P × L               carga puntual
\ ════════════════════════════════════════════════════════════════

\ Biapoyada + carga uniforme  (flecha máx. en centro)
: biapoyada
  5.0 384.0 /  _k1 !   1.0 8.0 /  _k2 !
  1 _tipoCarga !  1 _tipoApoyo !
;

\ Biapoyada + carga puntual en el centro
: biapoyada-puntual
  1.0 48.0 /  _k1 !   1.0 4.0 /  _k2 !
  2 _tipoCarga !  1 _tipoApoyo !
;

\ Biapoyada + carga puntual en posición _a  (usar a! antes)
: biapoyada-puntual-pos
  1.0 48.0 /  _k1 !   1.0 4.0 /  _k2 !
  3 _tipoCarga !  1 _tipoApoyo !
;

\ Empotrada en ambos extremos + carga uniforme
: empotrada
  1.0 384.0 /  _k1 !   1.0 12.0 /  _k2 !
  1 _tipoCarga !  2 _tipoApoyo !
;

\ Empotrada en ambos extremos + carga puntual en centro
: empotrada-puntual
  1.0 192.0 /  _k1 !   1.0 8.0 /  _k2 !
  2 _tipoCarga !  2 _tipoApoyo !
;

\ Empotrada-apoyada (ménsula apoyada) + carga uniforme
: empotrada-apoyada
  1.0 185.0 /  _k1 !   3.0 8.0 /  _k2 !
  1 _tipoCarga !  4 _tipoApoyo !
;

\ Voladizo + carga uniforme  (flecha máx. en extremo libre)
: voladizo
  1.0 8.0 /  _k1 !   1.0 2.0 /  _k2 !
  1 _tipoCarga !  3 _tipoApoyo !
;

\ Voladizo + carga puntual en el extremo libre
: voladizo-puntual
  1.0 3.0 /  _k1 !   1.0 1.0 /  _k2 !
  2 _tipoCarga !  3 _tipoApoyo !
;

\ ── Setters simples ──────────────────────────────────────────────

: L!   ( mm -- )     _l ! ;
: q!   ( N/mm -- )   _q ! ;
: P!   ( N -- )      _P ! ;
: a!   ( mm -- )     _a ! ;
: I!   ( mm4 -- )    _i ! ;
: W!   ( mm3 -- )    _W ! ;
: E!   ( N/mm2 -- )  _E ! ;

\ Fija el límite de flecha como L/n  (ej. 300 flim! → L/300)
: flim!  ( n -- )   _l @  swap  /  _fLim ! ;

\ ── Ayudantes internos ───────────────────────────────────────────

\ L⁴: usa (L²)² — correcto: L dup* = L², luego L² dup* = L⁴
: _L4  ( -- L4 )   _l @ dup *  dup * ;

\ L³: usa x dup dup * * — correcto: L L L → L L² → L³
: _L3  ( -- L3 )   _l @ dup dup * * ;

\ L²
: _L2  ( -- L2 )   _l @ dup * ;

\ E × I
: _EI  ( -- EI )   _E @ _i @ * ;

\ Fuerza total efectiva
: _Qef  ( -- Q )
  _tipoCarga @ 1 = if  _q @ _l @ *
  else  _P @
  then
;

\ ════════════════════════════════════════════════════════════════
\  Cálculos bidireccionales
\  Sin argumento → calcula e imprime
\  Con argumento → fija el valor (para problemas inversos)
\ ════════════════════════════════════════════════════════════════

\ Flecha máxima [mm]
: flecha  ( -- | mm -- )
  depth 0 = if
    _tipoCarga @ 1 = if
      _k1 @  _q @  _L4  *  *  _EI  /
    else
      _k1 @  _P @  _L3  *  *  _EI  /
    then
    dup  _f !
    ." f = " .  ." mm"
    _fLim @ 0.0 > if
      ."   |  limite = " _fLim @ .  ." mm"
      _f @ _fLim @ <= if  ."   → OK" else  ."   → NO CUMPLE" then
    then
    cr
  else
    _f !
  then
;

\ Longitud máxima [mm] para la flecha fijada en _f  (carga uniforme)
\   L = (f × E × I / (k1 × q)) ^ 0.25
: longitud  ( -- | mm -- )
  depth 0 = if
    _f @  _EI  *  _k1 @  _q @  *  /  sqrt  sqrt
    dup  _l !
    ." L = " .  ." mm" cr
  else
    _l !
  then
;

\ Inercia mínima [mm⁴] para la flecha fijada en _f  (carga uniforme)
\   I = k1 × q × L⁴ / (f × E)
: inercia  ( -- | mm4 -- )
  depth 0 = if
    _k1 @  _q @  _L4  *  *  _f @  _E @  *  /
    dup  _i !
    ." I = " .  ." mm4" cr
  else
    _i !
  then
;

\ ── Cálculos unidireccionales ─────────────────────────────────

\ Momento máximo [N·mm]
: Mmax  ( -- )
  _tipoCarga @ 3 = if
    \ puntual en posición a: M = P × (L−a) × a / L
    _P @  _l @ _a @ -  *  _a @  *  _l @  /
  else
    _tipoCarga @ 1 = if
      _k2 @  _q @  _L2  *  *
    else
      _k2 @  _P @  *  _l @  *
    then
  then
  ." Mmax = " .  ." N.mm" cr
;

\ Cortante máximo [N]
: Vmax  ( -- )
  _tipoApoyo @ 3 = if
    _Qef                  \ voladizo: todo en el empotramiento
  else
    _Qef  2.0  /          \ biapoyada / empotrada: Q/2
  then
  ." Vmax = " .  ." N" cr
;

\ Reacciones R1 y R2 [N]
\  IMPORTANTE: no deja valores en la pila (todos los dup corregidos)
: reacciones  ( -- )
  _tipoCarga @ 3 = if
    \ carga puntual en posición a
    _P @  _l @ _a @ -  *  _l @  /  _R1 !
    _P @  _a @          *  _l @  /  _R2 !
  else
    _tipoApoyo @ 3 = if
      \ voladizo: solo reacción en el empotramiento
      _Qef  _R1 !   0.0  _R2 !
    else
      \ biapoyada / empotrada: R1 = R2 = Q/2
      _Qef  2.0  /  dup  _R1 !  _R2 !
    then
  then
  ." R1 = " _R1 @ .  ." N     R2 = " _R2 @ .  ." N" cr
;

\ Tensión máxima en fibra extrema [N/mm²]  (requiere _W definido)
: sigma  ( -- )
  _W @ 0.0 = if
    ." ERROR: W no definido — usa W! para fijar el módulo resistente" cr
    exit
  then
  _tipoCarga @ 1 = if
    _k2 @  _q @  _L2  *  *
  else
    _k2 @  _P @  *  _l @  *
  then
  _W @  /
  ." σ = " .  ." N/mm2" cr
;

\ Comprobación: flecha calculada vs límite _fLim
: verifica  ( -- )
  _tipoCarga @ 1 = if
    _k1 @  _q @  _L4  *  *  _EI  /
  else
    _k1 @  _P @  _L3  *  *  _EI  /
  then
  dup  _f !
  ." f_actual = " .  ." mm"
  _fLim @ 0.0 > if
    ."    f_limite = " _fLim @ .  ." mm"
    _f @ _fLim @ <= if  ."    → CUMPLE" else  ."    → NO CUMPLE" then
  then
  cr
;

\ ── Estado actual ────────────────────────────────────────────────
: estado  ( -- )
  cr
  ." ── Parámetros actuales ─────────────────────────" cr
  ." E   = " _E @   .  ." N/mm2     "
  ." fy  = " _fy @  .  ." N/mm2" cr
  ." I   = " _i @   .  ." mm4" cr
  ." L   = " _l @   .  ." mm" cr
  _tipoCarga @ 1 = if
    ." q   = " _q @  .  ." N/mm" cr
  else
    ." P   = " _P @  .  ." N" cr
    _tipoCarga @ 3 = if
      ." a   = " _a @  .  ." mm" cr
    then
  then
  ." k1  = " _k1 @  .  ."    k2 = " _k2 @ . cr
  ." f   = " _f @   .  ." mm"
  _fLim @ 0.0 > if  ."    f_lim = " _fLim @ .  ." mm" then  cr
  ." ─────────────────────────────────────────────────" cr
;

\ ── Ayuda ────────────────────────────────────────────────────────
: ayuda  ( -- )
  cr
  ." ════ Librería de Estructuras ══════════════════════" cr
  ." MATERIALES:  acero  aluminio  madera  hormigon" cr
  ." PERFILES:    ipe80..ipe600   heb100..heb600" cr
  ."              ipn100..ipn500  tubo(b h t --)" cr
  ." APOYOS:      biapoyada          biapoyada-puntual" cr
  ."              biapoyada-puntual-pos (fijar a! antes)" cr
  ."              empotrada          empotrada-puntual" cr
  ."              empotrada-apoyada" cr
  ."              voladizo           voladizo-puntual" cr
  ." SETTERS:     L!(mm)  q!(N/mm)  P!(N)  a!(mm)" cr
  ."              I!(mm4)  W!(mm3)   300 flim!  (L/n)" cr
  ." CÁLCULO:     flecha  longitud  inercia" cr
  ."              Mmax  Vmax  reacciones  sigma" cr
  ."              verifica  estado" cr
  ." BIDIRECCIONAL:" cr
  ."   flecha     → calcula flecha actual" cr
  ."   15.0 flecha → fija f = 15 mm" cr
  ."   300 flim!   → límite = L/300" cr
  ."   inercia    → I mínimo para f fijado" cr
  ."   longitud   → L máxima para f fijado" cr
  ." ════════════════════════════════════════════════════" cr
;
