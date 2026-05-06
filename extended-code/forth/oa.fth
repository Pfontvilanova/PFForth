\ Definiciones Forth guardadas automáticamente
\ Archivo: oa.fth

variable v1
variable v2
: int1 4 / v1 @ + v1 ! v1 @ ;
: int2 4 / v2 @ + v2 ! v2 @ ;
: negate 0 swap - ;
: init 0 v1 ! 0 v2 ! 100 ;
: osc-armonic int1 int2 negate ;
: spaces 0 do space loop ;
: disp 40 + floor spaces ." *" cr ;
: delay 0 do loop ;
: seno init 50 0 do osc-armonic dup disp loop cr ;
: buf-clear ( -- )
0 head ! 
0 tail ! 
0 count ! ;

\ Fin del archivo - 12 definiciones guardadas