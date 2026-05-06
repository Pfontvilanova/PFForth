\ ============================================================
\ demo-video.fth  —  Ver y analizar un video grabado
\ ============================================================
\
\ ANTES DE USAR:
\   1. Sube el video al directorio del proyecto (Replit: arrastra al panel)
\      o en iPad copia a ~/Documents/
\   2. Carga el vocabulario y este archivo:
\        IMPORT code/camera
\        s" demo-video" load
\
\ FORMATOS SOPORTADOS: mp4, avi, mkv, mov*
\   (*mov puede necesitar conversion en Linux/Replit:
\    ffmpeg -i video.mov salida.mp4)
\ ============================================================


\ ------------------------------------------------------------
\ Helpers internos: modo silencioso para analisis en batch
\ ------------------------------------------------------------

: vision-silent
  py{
  if not hasattr(forth, '_ai'): forth._ai = {}
  forth._ai['_silent'] = True
  forth._ai['_total_counts'] = {}
  }py ;

: vision-verbose
  py{
  if not hasattr(forth, '_ai'): forth._ai = {}
  forth._ai['_silent'] = False
  }py ;

: vision-summary
  py{
  if not hasattr(forth, '_ai'): forth._ai = {}
  counts = forth._ai.get('_total_counts', {})
  if counts:
      print(f"Maximo simultaneo por tipo de objeto:")
      print(f"  {'Objeto':<20} {'Max en un frame':>15}")
      print(f"  {'─'*20} {'─'*15}")
      for lbl, cnt in sorted(counts.items(), key=lambda x: -x[1]):
          print(f"  {lbl:<20} {cnt:>15}")
  else:
      print("No se detectaron objetos en el video")
  }py ;


\ ------------------------------------------------------------
\ Palabra 1: Solo VER el video (sin deteccion)
\ Uso: s" mi-video.mp4" ver-video
\ ------------------------------------------------------------
: ver-video ( filename -- )
  cam-open
  cam-open? 0= if
    ." Error: no se pudo abrir el video" cr exit
  then
  ." Reproduciendo — pulsa q para salir" cr
  cam-preview
  cam-close ;


\ ------------------------------------------------------------
\ Palabra 2: VER el video CON deteccion de personas
\ Marca las personas en pantalla y muestra cuando aparece una
\ Uso: s" mi-video.mp4" ver-video-personas
\ ------------------------------------------------------------
: ver-video-personas ( filename -- )
  cam-open
  cam-open? 0= if
    ." Error: no se pudo abrir el video" cr exit
  then
  cam-bg-init
  ." Analizando video — pulsa q para salir" cr
  ." Buscando personas..." cr
  begin
    cam-read
    0= if
      ." Fin del video" cr
      cam-window-close
      cam-close
      exit
    then
    cam-show
    500 cam-motion? if
      cam-person? if
        cam-pos . ." ms — persona detectada" cr
      then
    then
  key? until
  cam-window-close
  cam-close
  ." Analisis terminado" cr ;


\ ------------------------------------------------------------
\ Palabra 3: SOLO ANALIZAR sin mostrar ventana
\ Recorre todo el video en silencio y al final muestra
\ el total de objetos detectados con su listado.
\ Ideal en Replit / iPad / servidor sin pantalla.
\ Uso: s" mi-video.mp4" analizar-video
\ ------------------------------------------------------------
: analizar-video ( filename -- )
  cam-open
  cam-open? 0= if
    ." Error: no se pudo abrir el video" cr exit
  then
  cam-info
  cam-bg-init
  vision-silent
  ." Analizando video en silencio..." cr
  ." (puede tardar segun la duracion)" cr
  0
  begin
    cam-read
    0= if
      vision-verbose
      cr ." ========================================" cr
      ." Frames con detecciones: " . cr
      vision-summary
      ." ========================================" cr
      drop
      cam-close
      exit
    then
    500 cam-motion? if
      cam-person? if
        1 +
      then
    then
  again ;


\ ------------------------------------------------------------
\ EJEMPLOS DE USO
\ ------------------------------------------------------------
\
\   Solo ver el video:
\     s" video.mp4" ver-video
\
\   Ver con deteccion de personas (en pantalla):
\     s" video.mp4" ver-video-personas
\
\   Analizar sin ventana (Replit, iPad, servidor):
\     s" video.mp4" analizar-video
\
\   Ir a un momento concreto y ver desde ahi:
\     s" video.mp4" cam-open
\     cam-open? if
\       90000 cam-seek         \ salta al minuto 1:30
\       cam-preview
\       cam-close
\     then
\ ============================================================
