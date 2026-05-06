\ ============================================
\ RELOJ ANALOGICO - pfForth 
\ ============================================
\ Uso: LOAD reloj
\ ============================================

import code/graphics
import code/tools

\ --- Parametros del reloj ---
120 value reloj-ancho
120 value reloj-alto
60 value cx
60 value cy
55 value radio-esfera

\ --- Abrir ventana ---
reloj-ancho reloj-alto canvas-new

\ --- Convertir grados a radianes ---
: deg>rad  pi * 180.0 / ;

\ ( angulo_grados longitud -- x )
: ang>x  swap deg>rad sin * floor cx + ;

\ ( angulo_grados longitud -- y )
: ang>y  swap deg>rad cos negate * floor cy + ;

\ --- Dibujar marca de hora ---
\ ( angulo_grados -- )
: marca-hora
  1 line-width
  255 255 255 pen-color
  dup 48 ang>x over 48 ang>y
  rot dup 55 ang>x swap 55 ang>y
  line
;

\ --- Dibujar numero de hora ---
\ ( hora angulo_grados -- )
: num-hora
  dup 42 ang>x 1 -
  swap 42 ang>y 2 -
  rot >str
  10 swap canvas-text
;

\ --- Dibujar manecilla ---
\ ( ang lon grosor r g b -- )
: manecilla
  pen-color
  line-width
  2dup
  ang>x -rot
  ang>y
  cx cy 2swap
  line
;

\ --- Dibujar esfera completa ---
: esfera
  255 255 255 pen-color
  1 line-width
  -1 -1 -1 fill-color
  cx cy radio-esfera circle

  12 0 do
    i 30 * marca-hora
  loop

  12 0 do
    i 0= if 12 else i then
    i 30 * num-hora
  loop
;

\ --- Obtener hora actual ---
\ ( -- hora minuto segundo )
: hora-actual
  py{
import time
t = time.localtime()
push(t.tm_hour + 1)
push(t.tm_min)
push(t.tm_sec)
}py
;

\ --- Dibujar reloj completo ---
: dibujar-reloj
  canvas-clear
  esfera

  hora-actual

  dup 6 *
  45 1 255 255 255 manecilla

  over 6 *
  38 1 255 0 255 manecilla

  drop
  dup 2 /
  rot 12 mod 30 * +
  28 2 255 255 0 manecilla
  drop

  canvas-update
;

\ --- Bucle principal ---
: reloj
  ." Reloj iniciado. Pulsa Ctrl-C para parar." cr
  1000 ms
  begin
    dibujar-reloj
    1000 ms
  again
;

\ --- Ejecutar ---
