\ Definiciones Forth guardadas automáticamente
\ Archivo: simul/simulacio.fth
\ simula la velocidad en el tiempo de una masa de 1500 kg con una fuerza de 5000N.
\ usa la ecuacion diferencial del movimiento.
variable vi
variable ui
variable dt
variable m
variable fr
5000.0 ui !
1500 m !
0.5 fr !
1 dt !
0 vi !
: init 0 vi ! ;
: 1/m 1.0 m @ / ;
: b/m fr @ m @ / ;
: num dt @ 1/m * ui @ * vi @ + ;
: denom dt @ b/m * 1 + ;
: 1/s num denom / vi ! ;
: simul 10 0 do 1/s vi @ . cr loop init ;

\ Fin del archivo - 12 definiciones guardadas
