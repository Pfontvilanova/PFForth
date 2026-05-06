\ ============================================
\ RELOJ DIGITAL - pfForth 
\ ============================================
\ Uso: S" forth/time" LOAD 
\ ============================================

\ --- Obtener hora actual ---
\ ( -- hora minuto segundo )
: hora-actual
  py{
import time
t = time.localtime()
push(t.tm_hour)
push(t.tm_min)
push(t.tm_sec)
}py
;

\ --- Bucle principal ---
: time
 hora-actual -rot swap ." Hora:" . ." Min:" . ." sg:" . cr
;






