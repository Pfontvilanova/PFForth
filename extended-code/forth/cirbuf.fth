\ Parámetros
variable buf-size   8 buf-size !
create w 8 cells allot
\ Punteros y contador
variable head  0 head !
variable tail  0 tail !
variable count 0 count !
\ Helpers
: next ( n -- n' ) 1+ buf-size @ mod ;
\ ¿Está lleno?
: buf-full? ( -- flag ) count @ buf-size @ = ;
\ ¿Está vacío?
: buf-empty? ( -- flag ) count @ 0= ;
\ Escribir un valor (si no está lleno)
: w! ( n -- )
  count @ buf-size @ < if
    tail @ cells w + !         \ Escribe en buffer[tail]
    tail @ next tail !         \ Avanza tail
    count @ 1+ count !         \ Incrementa contador
  else
    ." full buffer, read before write again" cr
  then ;
: reset-w ( -- )
   0 count ! 0 tail ! 0 head !
   w buf-size @ + w do 0 i m! loop ;
\ Leer un valor (si no está vacío)
: w@ ( -- n )
  count @ 0 > if
    head @ cells w + @         \ Lee buffer[head]
    head @ next head !         \ Avanza head
    count @ 1- count !         \ Decrementa contador
  else
    ." buffer vacio" cr 0
  then ;
\ Mostrar estado (opcional)
: w? ( -- )
  ." Head: " head @ . 
  ." Tail: " tail @ . 
  ." Count: " count @ . cr ;
: .w ( -- )
  w buf-size @ dump ;
  
  
 
    