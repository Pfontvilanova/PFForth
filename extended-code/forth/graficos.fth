\ ============================================
\ DEMO GRAFICA RETRO - Estilo primeros ordenadores
\ Uso: import code/graphics
\      LOAD demos/graficos
\ ============================================

160 80 canvas-new
cursor-off
0 0 0 canvas-bg
canvas-clear
canvas-update

: espera  py{ import time; time.sleep(0.1) }py ;
: sin-fill  -1 -1 -1 fill-color ;

\ ============================================
\ ESCENA 1: Lineas radiantes desde el centro
\ ============================================
: escena-lineas
  1 line-width  sin-fill

  \ Diagonales verdes
  0 220 0 pen-color
  0 0 160 80 line   canvas-update espera
  160 0 0 80 line   canvas-update espera

  \ Cruz naranja
  255 140 0 pen-color
  80 0 80 80 line   canvas-update espera
  0 40 160 40 line  canvas-update espera

  \ Diagonales cyan
  0 200 255 pen-color
  0 20 160 60 line  canvas-update espera
  0 60 160 20 line  canvas-update espera
  40 0 120 80 line  canvas-update espera
  120 0 40 80 line  canvas-update espera
;

\ ============================================
\ ESCENA 2: Circulos concentricos
\ ============================================
: escena-circulos
  sin-fill  1 line-width

  255 255 0 pen-color   80 40 36 circle  canvas-update espera
  255 0 255 pen-color   80 40 27 circle  canvas-update espera
  0 255 255 pen-color   80 40 18 circle  canvas-update espera
  255 80 0  pen-color   80 40  9 circle  canvas-update espera

  \ Circulo relleno central
  255 255 255 pen-color
  200 200 200 fill-color
  80 40 4 circle
  sin-fill
  canvas-update espera
;

\ ============================================
\ ESCENA 3: Rectangulos de colores
\ ============================================
: escena-rects
  sin-fill  2 line-width

  255   0   0 pen-color   5  5 72 35 box  canvas-update espera
    0 255   0 pen-color  83  5 72 35 box  canvas-update espera
    0  80 255 pen-color   5 42 72 35 box  canvas-update espera
  255 220   0 pen-color  83 42 72 35 box  canvas-update espera

  \ Pequeños rellenos en el centro
  1 line-width
  255 60 0 pen-color
  255 30 0 fill-color
  65 30 30 20 filled-box
  sin-fill
  canvas-update espera
;

\ ============================================
\ ESCENA 4: Simetria - circulos en esquinas
\ ============================================
: escena-simetria
  1 line-width  sin-fill

  \ Cruz blanca central
  255 255 255 pen-color
  60 40 40 hline  canvas-update espera
  80 28 24 vline  canvas-update espera

  \ Circulos esquinas amarillos
  255 200 0 pen-color
  14 14 10 circle  canvas-update espera
  146 14 10 circle canvas-update espera
  14 66 10 circle  canvas-update espera
  146 66 10 circle canvas-update espera

  \ Circulos bordes cyan
  0 255 180 pen-color
  80  7  6 circle  canvas-update espera
  80 73  6 circle  canvas-update espera
   7 40  6 circle  canvas-update espera
  153 40  6 circle canvas-update espera
;

\ ============================================
\ ESCENA 5: Cuadrados rotados en el centro
\ ============================================
: escena-rotados
  2 line-width  sin-fill

  255   0   0 pen-color    0 box-angle  60 30 40 20 box  canvas-update espera
    0 100 255 pen-color   15 box-angle  60 30 40 20 box  canvas-update espera
  255 255   0 pen-color   30 box-angle  60 30 40 20 box  canvas-update espera
    0 255  80 pen-color   45 box-angle  60 30 40 20 box  canvas-update espera
  255   0 200 pen-color   60 box-angle  60 30 40 20 box  canvas-update espera
  255 255 255 pen-color   75 box-angle  60 30 40 20 box  canvas-update espera

  0 box-angle
  1 line-width
;

\ ============================================
\ ESCENA 6: Puntos simetricos (estilo Amiga)
\ ============================================
: escena-puntos
  sin-fill  1 line-width
  0 200 0  pen-color   20 10 3 circle  canvas-update espera
  0 200 0  pen-color  140 10 3 circle  canvas-update espera
  0 200 0  pen-color   20 70 3 circle  canvas-update espera
  0 200 0  pen-color  140 70 3 circle  canvas-update espera

  255 0 100 pen-color   50 10 3 circle  canvas-update espera
  255 0 100 pen-color  110 10 3 circle  canvas-update espera
  255 0 100 pen-color   50 70 3 circle  canvas-update espera
  255 0 100 pen-color  110 70 3 circle  canvas-update espera

  100 100 255 pen-color  80 10 3 circle  canvas-update espera
  100 100 255 pen-color  80 70 3 circle  canvas-update espera
  100 100 255 pen-color  20 40 3 circle  canvas-update espera
  100 100 255 pen-color 140 40 3 circle  canvas-update espera
;

\ ============================================
\ TITULO FINAL
\ ============================================
: titulo
  255 255 255 pen-color
  20 1 2 s" * FORTH GRAPHICS DEMO *" canvas-text
  canvas-update
;

\ ============================================
\ PROGRAMA PRINCIPAL
\ ============================================
: demo
  canvas-clear canvas-update
  espera espera

  escena-lineas
  espera

  escena-circulos
  espera

  escena-rects
  espera

  escena-simetria
  espera

  escena-rotados
  espera

  escena-puntos
  espera espera

  titulo
  cursor-on
;

demo
