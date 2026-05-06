\ ============================================================
\ wifi-stream.fth  —  Streaming cam/video a cualquier navegador
\ ============================================================
\
\ Streaming en segundo plano (el REPL queda libre) accesible
\ desde la red local y, con port-forwarding en el router,
\ desde cualquier navegador en internet.
\
\ PALABRAS:
\   cam-stream-start              ( -- )        streaming de camara
\   cam-stream-stop               ( -- )        para el streaming
\   s" video.mp4" video-stream-start ( src -- ) streaming de video
\   video-stream-stop             ( -- )        para el streaming
\
\ REQUISITOS:
\   IMPORT code/camera        \ carga vocabulario de camara (primero)
\   s" wifi-stream" LOAD      \ carga este fichero
\
\ USO TIPICO:
\   0 cam-open
\   cam-stream-start
\   ... ( REPL libre mientras el stream esta activo )
\   cam-stream-stop
\
\   s" video.mp4" video-stream-start
\   video-stream-stop
\
\ RED LOCAL:
\   Abre  http://<IP-local>:8765  en cualquier dispositivo del mismo wifi.
\   En iPad/Mac/RPi el OS ya gestiona el wifi; no hace falta wifi-connect.
\
\ INTERNET:
\   1. Accede al panel de tu router (normalmente http://192.168.1.1)
\   2. Crea una regla de port-forward: puerto 8765 -> IP-local del equipo
\   3. Comparte tu IP publica (whatismyip.com) con quien quiera ver el stream
\
\ ESP32 / microcontroladores sin OS:
\   s" MiRed" s" mipassword" wifi-connect   \ conectar primero
\   luego usar las palabras normalmente
\ ============================================================


\ --- Variables de configuracion ---
variable wifi-stream-port   8765 wifi-stream-port !
variable wifi-stream-actor     0 wifi-stream-actor !
variable wifi-video-actor      0 wifi-video-actor !


\ ============================================================
\ Actor: STREAMING DE CAMARA EN VIVO
\ El actor corre en hilo propio; el REPL queda libre.
\ Reutiliza _start_mjpeg_server / _stop_mjpeg_server de _cam.py
\ ============================================================

: _cam-stream-body
  py{
  import sys, time, socket, importlib.util as _ilu, os as _os
  import queue as _qmod

  h = sys.modules.get('_cam_helper')
  if h is None:
      _cp = _os.path.join(forth._base_dir, 'extended-code', 'code', 'camera', '_cam.py')
      if _os.path.isfile(_cp):
          _spec = _ilu.spec_from_file_location('_cam_helper', _cp)
          h = _ilu.module_from_spec(_spec)
          sys.modules['_cam_helper'] = h
          _spec.loader.exec_module(h)
  if h is None:
      print("Error cam-stream: usa IMPORT code/camera antes de cargar wifi-stream")
  else:
      cfg  = sys.modules.get('_wifi_stream_state', {})
      cap  = cfg.get('cap')
      port = cfg.get('port', 8765)

      if cap is None:
          print("Error cam-stream: no hay camara abierta — usa 0 cam-open primero")
      else:
          # Prepara forth._cam del actor hijo con la camara compartida del padre
          h._ensure_cam(forth)
          forth._cam['cap']    = cap
          forth._cam['source'] = cfg.get('source')

          # Tracking de clientes conectados por IP
          _clients = {}

          def on_connect(addr):
              ip = addr[0]
              if ip not in _clients:
                  _clients[ip] = True
                  print(f"+ Espectador conectado: {ip}")

          def on_disconnect(addr):
              ip = addr[0]
              if ip in _clients:
                  del _clients[ip]
                  print(f"+ Espectador desconectado: {ip}")

          try:
              srv = h._start_mjpeg_server(forth, port,
                                          on_connect=on_connect,
                                          on_disconnect=on_disconnect)
          except TypeError:
              srv = h._start_mjpeg_server(forth, port)
          if srv:
              lip = h._get_local_ip()
              print(f"+ Streaming de camara activo  (REPL libre)")
              print(f"  Red local:  http://{lip}:{port}")
              print(f"  Internet:   configura port-forward {port} -> {lip} en tu router")
              print(f"  Para parar: cam-stream-stop")

              try:
                  from pfforth.actors import _KILL_SENTINEL as _KS
              except Exception:
                  _KS = None

              while True:
                  ret, frame = cap.read()
                  if not ret:
                      print("+ cam-stream: camara desconectada")
                      break
                  forth._cam['frame'] = frame
                  try:
                      msg = forth._actor_queue.get_nowait()
                      if _KS is not None and msg is _KS:
                          break
                      forth._actor_queue.put(msg)
                  except _qmod.Empty:
                      pass
                  except Exception:
                      break
                  time.sleep(0.033)

              h._stop_mjpeg_server(forth)
              print("+ cam-stream detenido")
  }py ;


: cam-stream-start  ( -- )
  py{ forth.stack.append(-1 if getattr(forth,'_cam',{}).get('cap') is not None else 0) }py
  0= if
    ." Error: no hay camara abierta — usa 0 cam-open primero" cr exit
  then
  py{
  import sys
  sys.modules['_wifi_stream_state'] = {
      'cap':    forth._cam.get('cap'),
      'source': forth._cam.get('source'),
      'port':   int(forth.variables.get('wifi-stream-port', 8765)),
  }
  }py
  s" _cam-stream-body" actor-spawn
  dup wifi-stream-actor !
  actor-run ;


: cam-stream-stop  ( -- )
  wifi-stream-actor @ dup 0= if
    drop ." cam-stream no esta activo" cr exit
  then
  actor-kill
  0 wifi-stream-actor ! ;


\ ============================================================
\ Actor: STREAMING DE VIDEO (fichero, reproduccion en bucle)
\ Reutiliza _start_mjpeg_server / _stop_mjpeg_server de _cam.py
\ ============================================================

: _video-stream-body
  py{
  import cv2, sys, time, socket, importlib.util as _ilu, os as _os
  import queue as _qmod

  h = sys.modules.get('_cam_helper')
  if h is None:
      _cp = _os.path.join(forth._base_dir, 'extended-code', 'code', 'camera', '_cam.py')
      if _os.path.isfile(_cp):
          _spec = _ilu.spec_from_file_location('_cam_helper', _cp)
          h = _ilu.module_from_spec(_spec)
          sys.modules['_cam_helper'] = h
          _spec.loader.exec_module(h)
  if h is None:
      print("Error video-stream: usa IMPORT code/camera antes de cargar wifi-stream")
  else:
      cfg  = sys.modules.get('_wifi_stream_state', {})
      src  = cfg.get('video_src')
      port = cfg.get('port', 8765)

      if not src:
          print("Error video-stream: no hay fuente de video configurada")
      else:
          cap = cv2.VideoCapture(str(src))
          if not cap.isOpened():
              print(f"Error video-stream: no se pudo abrir '{src}'")
          else:
              fps_src = cap.get(cv2.CAP_PROP_FPS)
              if not (5 <= fps_src <= 120):
                  fps_src = 25.0
              delay = 1.0 / fps_src

              # Prepara forth._cam del actor hijo con el video como fuente
              h._ensure_cam(forth)
              forth._cam['cap']    = cap
              forth._cam['source'] = str(src)

              # Tracking de clientes conectados por IP
              _clients = {}

              def on_connect(addr):
                  ip = addr[0]
                  if ip not in _clients:
                      _clients[ip] = True
                      print(f"+ Espectador conectado: {ip}")

              def on_disconnect(addr):
                  ip = addr[0]
                  if ip in _clients:
                      del _clients[ip]
                      print(f"+ Espectador desconectado: {ip}")

              try:
                  srv = h._start_mjpeg_server(forth, port,
                                              on_connect=on_connect,
                                              on_disconnect=on_disconnect)
              except TypeError:
                  srv = h._start_mjpeg_server(forth, port)
              if srv:
                  import os
                  lip = h._get_local_ip()
                  print(f"+ Streaming de video activo  (REPL libre)")
                  print(f"  Fichero:    {os.path.basename(str(src))}")
                  print(f"  Red local:  http://{lip}:{port}")
                  print(f"  Internet:   configura port-forward {port} -> {lip} en tu router")
                  print(f"  Para parar: video-stream-stop")

                  try:
                      from pfforth.actors import _KILL_SENTINEL as _KS
                  except Exception:
                      _KS = None

                  loop_count = 0
                  while True:
                      t0 = time.time()
                      ret, frame = cap.read()
                      if not ret:
                          loop_count += 1
                          cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                          ret, frame = cap.read()
                          if not ret:
                              print("+ video-stream: no se puede releer el video")
                              break
                          if loop_count == 1:
                              print("+ Video en bucle (video-stream-stop para parar)")
                      forth._cam['frame'] = frame
                      try:
                          msg = forth._actor_queue.get_nowait()
                          if _KS is not None and msg is _KS:
                              break
                          forth._actor_queue.put(msg)
                      except _qmod.Empty:
                          pass
                      except Exception:
                          break
                      elapsed = time.time() - t0
                      rest = delay - elapsed
                      if rest > 0:
                          time.sleep(rest)

                  h._stop_mjpeg_server(forth)
                  cap.release()
                  print("+ video-stream detenido")
  }py ;


: video-stream-start  ( src -- )
  py{
  import sys, os
  src = forth.stack.pop()
  resolved = str(src)
  for candidate in [str(src),
                    os.path.join(os.getcwd(), str(src)),
                    os.path.expanduser(os.path.join('~', str(src))),
                    os.path.expanduser(os.path.join('~', 'Documents', str(src)))]:
      if os.path.isfile(candidate):
          resolved = os.path.abspath(candidate)
          break
  sys.modules['_wifi_stream_state'] = {
      'video_src': resolved,
      'port': int(forth.variables.get('wifi-stream-port', 8765)),
  }
  }py
  s" _video-stream-body" actor-spawn
  dup wifi-video-actor !
  actor-run ;


: video-stream-stop  ( -- )
  wifi-video-actor @ dup 0= if
    drop ." video-stream no esta activo" cr exit
  then
  actor-kill
  0 wifi-video-actor ! ;
