\ ============================================================
\ wifi-send.fth  —  Transferencia TCP de ficheros y texto
\ ============================================================
\
\ Envía ficheros o texto a cualquier dispositivo con pfforth
\ mediante TCP. Los actores corren en segundo plano para que
\ el REPL no se bloquee durante la transferencia.
\
\ PALABRAS:
\   wifi-send-start                            ( -- )   actor emisor
\   s" IP" s" ruta/fichero.jpg" wifi-send      ( ip src -- ) envía fichero
\   s" IP" s" Hola desde iPad" wifi-send       ( ip src -- ) envía texto
\   s" IP" 42 wifi-send                        ( ip n -- )  envía número
\   wifi-send-stop                             ( -- )   para el emisor
\
\   wifi-recv-start                            ( -- )   servidor receptor
\   wifi-recv-stop                             ( -- )   para el servidor
\
\ PROGRESO EN TIEMPO REAL:
\   Durante el envío de ficheros se imprime progreso periódico:
\     + Enviando: foto.jpg  45%  (1.1 / 2.4 MB) -> 192.168.1.50
\   Al completar se imprime velocidad media:
\     + Enviado: foto.jpg (2.4 MB @ 3.2 MB/s) -> 192.168.1.50
\   Frecuencia configurable (por defecto cada 2 segundos):
\     5 wifi-send-progress-s !
\
\ PROTOCOLO TCP:
\   Cabecera JSON terminada en newline:
\     {"v":1,"type":"file"|"text","name":"...","size":N}
\   seguida de N bytes de payload.
\
\ REQUISITOS:
\   s" wifi-send" LOAD
\   (No requiere IMPORT code/camera, aunque lo usa si esta disponible)
\
\ USO TIPICO (dos equipos en la misma red):
\
\   --- RECEPTOR (equipo A, IP 192.168.1.50) ---
\   s" wifi-send" LOAD
\   wifi-recv-start
\     + Escuchando en 192.168.1.50:9876
\
\   --- EMISOR (equipo B) ---
\   s" wifi-send" LOAD
\   wifi-send-start
\   s" 192.168.1.50" s" ~/Documents/foto.jpg" wifi-send
\     + Enviado: foto.jpg (1.2 MB) -> 192.168.1.50
\
\   s" 192.168.1.50" s" Hola desde iPad" wifi-send
\     + Enviado: texto (16 bytes) -> 192.168.1.50
\
\   s" 192.168.1.50" 42 wifi-send
\     + Enviado: texto (2 bytes) -> 192.168.1.50
\
\   wifi-send-stop
\
\ INTERNET:
\   En el receptor: configura port-forward de wifi-recv-port (9876)
\   en el router hacia la IP local del receptor.
\   En el emisor: usa la IP publica del receptor en wifi-send.
\
\ ESP32 / microcontroladores sin OS:
\   s" MiRed" s" password" wifi-connect   \ conectar a wifi primero
\ ============================================================


\ --- Variables de configuracion ---
variable wifi-send-port       9876 wifi-send-port !
variable wifi-recv-port       9876 wifi-recv-port !
variable wifi-send-actor         0 wifi-send-actor !
variable wifi-recv-actor         0 wifi-recv-actor !
variable wifi-send-progress-s    2 wifi-send-progress-s !  \ intervalo de progreso en segundos


\ ============================================================
\ Actor: EMISOR TCP
\ Bucle receive: espera mensajes [ip, data], abre socket y envía.
\ Detecta automáticamente si data es ruta de fichero o texto.
\ ============================================================

: _wifi-send-body
  py{
  import sys, json, socket, os
  import queue as _qmod

  try:
      from pfforth.actors import _KILL_SENTINEL as _KS
  except Exception:
      _KS = None

  import time as _time

  port         = int(forth.variables.get('wifi-send-port', 9876))
  print(f"+ Actor wifi-send listo (#{forth._actor_id_val})")

  while True:
      # Espera mensaje bloqueante; _KILL_SENTINEL llega cuando actor-kill
      msg = forth._actor_queue.get()
      if _KS is not None and msg is _KS:
          break

      value = msg.value if hasattr(msg, 'value') else msg

      if not isinstance(value, (list, tuple)) or len(value) < 2:
          print(f"Error wifi-send: mensaje invalido: {value}")
          continue

      ip       = str(value[0])
      data     = value[1]
      data_str = str(data)

      # Detecta si data_str es ruta de fichero existente
      is_file  = False
      filepath = None
      for candidate in [
              data_str,
              os.path.expanduser(data_str),
              os.path.join(os.getcwd(), data_str),
              os.path.expanduser(os.path.join('~', 'Documents', data_str)),
      ]:
          if os.path.isfile(candidate):
              is_file  = True
              filepath = os.path.abspath(candidate)
              break

      sock = None
      try:
          sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
          sock.settimeout(10.0)
          sock.connect((ip, port))

          if is_file:
              fname     = os.path.basename(filepath)
              fsize     = os.path.getsize(filepath)
              hdr       = json.dumps({"v": 1, "type": "file",
                                      "name": fname, "size": fsize}) + "\n"
              sock.sendall(hdr.encode('utf-8'))

              try:
                  progress_s = float(forth.variables.get('wifi-send-progress-s', 2))
              except (TypeError, ValueError):
                  progress_s = 2.0
              if progress_s < 0.2:
                  progress_s = 0.2
              sent         = 0
              t_start      = _time.monotonic()
              t_last       = t_start

              with open(filepath, 'rb') as f:
                  while True:
                      chunk = f.read(65536)
                      if not chunk:
                          break
                      sock.sendall(chunk)
                      sent += len(chunk)

                      now = _time.monotonic()
                      if now - t_last >= progress_s and fsize > 0:
                          pct      = sent / fsize * 100
                          sent_mb  = sent  / 1048576
                          total_mb = fsize / 1048576
                          print(f"+ Enviando: {fname}  {pct:.0f}%"
                                f"  ({sent_mb:.1f} / {total_mb:.1f} MB) -> {ip}")
                          t_last = now

              elapsed = _time.monotonic() - t_start
              total_mb = fsize / 1048576
              speed_mb = total_mb / elapsed if elapsed > 0 else 0
              print(f"+ Enviado: {fname} ({total_mb:.1f} MB @ {speed_mb:.1f} MB/s) -> {ip}")

          else:
              payload = data_str.encode('utf-8')
              hdr     = json.dumps({"v": 1, "type": "text",
                                    "name": "", "size": len(payload)}) + "\n"
              sock.sendall(hdr.encode('utf-8'))
              sock.sendall(payload)
              print(f"+ Enviado: texto ({len(payload)} bytes) -> {ip}")

      except Exception as e:
          print(f"Error wifi-send -> {ip}: {e}")
      finally:
          if sock:
              try:
                  sock.close()
              except Exception:
                  pass

  print("+ wifi-send actor detenido")
  }py ;


: wifi-send-start  ( -- )
  wifi-send-actor @ 0<> if
    ." wifi-send ya esta activo (usa wifi-send-stop primero)" cr exit
  then
  s" _wifi-send-body" actor-spawn
  dup wifi-send-actor !
  actor-run ;


: wifi-send  ( ip src -- )
  wifi-send-actor @ 0= if
    ." Error: wifi-send no activo — usa wifi-send-start primero" cr
    2drop exit
  then
  py{
  src = forth.stack.pop()
  ip  = forth.stack.pop()
  forth.stack.append([str(ip), src])
  }py
  wifi-send-actor @ actor-send ;


: wifi-send-stop  ( -- )
  wifi-send-actor @ dup 0= if
    drop ." wifi-send no esta activo" cr exit
  then
  actor-kill
  0 wifi-send-actor ! ;


\ ============================================================
\ Actor: RECEPTOR TCP
\ Servidor en segundo plano; acepta una conexión cada vez,
\ guarda ficheros en el directorio actual o imprime textos.
\ ============================================================

: _wifi-recv-body
  py{
  import sys, json, socket, os, threading
  import queue as _qmod

  try:
      from pfforth.actors import _KILL_SENTINEL as _KS
  except Exception:
      _KS = None

  port = int(forth.variables.get('wifi-recv-port', 9876))

  # IP local: usa _cam_helper si esta cargado, sino fallback directo
  h = sys.modules.get('_cam_helper')
  if h and hasattr(h, '_get_local_ip'):
      lip = h._get_local_ip()
  else:
      try:
          _s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
          _s.connect(('8.8.8.8', 80))
          lip = _s.getsockname()[0]
          _s.close()
      except Exception:
          lip = '127.0.0.1'

  srv = None
  try:
      srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
      srv.bind(('0.0.0.0', port))
      srv.listen(5)
      srv.settimeout(1.0)   # timeout breve para comprobar kill signal
  except OSError as e:
      print(f"Error wifi-recv: no se pudo iniciar en puerto {port}: {e}")
      srv = None

  if srv:
      print(f"+ Servidor wifi-recv activo")
      print(f"  Escuchando en {lip}:{port}")
      print(f"  Internet: configura port-forward {port} -> {lip} en tu router")
      print(f"  Para parar: wifi-recv-stop")

      MAX_HDR_BYTES  = 4096              # cabecera JSON max 4 KB
      MAX_FILE_BYTES = 500 * 1024 * 1024  # fichero max 500 MB
      MAX_TEXT_BYTES =   1 * 1024 * 1024  # texto max 1 MB

      def _safe_filename(raw):
          """Devuelve solo el basename; rechaza vacío, '.' y '..'."""
          safe = os.path.basename(raw.replace('\\', '/').strip())
          if not safe or safe in ('.', '..'):
              safe = 'recibido'
          return safe

      def _handle(conn, addr):
          save_path = None
          try:
              # Lee cabecera JSON terminada en newline (max MAX_HDR_BYTES)
              buf = b''
              while b'\n' not in buf:
                  chunk = conn.recv(min(256, MAX_HDR_BYTES - len(buf)))
                  if not chunk:
                      return
                  buf += chunk
                  if len(buf) >= MAX_HDR_BYTES:
                      print(f"Error wifi-recv: cabecera demasiado grande de {addr[0]}")
                      return
              nl        = buf.index(b'\n')
              hdr       = json.loads(buf[:nl].decode('utf-8'))
              remaining = buf[nl + 1:]

              if hdr.get('v') != 1:
                  print(f"Aviso wifi-recv: protocolo desconocido de {addr[0]}")
                  return

              ftype = hdr.get('type')
              fname = hdr.get('name', 'recibido')
              fsize = int(hdr.get('size', 0))

              if fsize < 0:
                  print(f"Error wifi-recv: tamaño negativo de {addr[0]}")
                  return

              if ftype == 'file':
                  if fsize > MAX_FILE_BYTES:
                      print(f"Error wifi-recv: fichero demasiado grande "
                            f"({fsize // 1048576} MB > 500 MB) de {addr[0]}")
                      return

                  # Sanitiza nombre: solo basename, sin traversal
                  safe_name = _safe_filename(fname)
                  save_path = os.path.join(os.getcwd(), safe_name)

                  # Escribe a disco en chunks (no buffering en memoria)
                  received = 0
                  with open(save_path, 'wb') as f:
                      if remaining:
                          f.write(remaining[:fsize])
                          received += min(len(remaining), fsize)
                      while received < fsize:
                          to_read = min(65536, fsize - received)
                          chunk = conn.recv(to_read)
                          if not chunk:
                              break
                          f.write(chunk)
                          received += len(chunk)

                  if received < fsize:
                      print(f"Aviso wifi-recv: {safe_name} incompleto "
                            f"({received}/{fsize} bytes) de {addr[0]}")
                      try:
                          os.remove(save_path)
                      except Exception:
                          pass
                      save_path = None
                  else:
                      mb = received / 1048576
                      print(f"+ Fichero recibido: {safe_name} ({mb:.1f} MB) de {addr[0]}")

              elif ftype == 'text':
                  if fsize > MAX_TEXT_BYTES:
                      print(f"Error wifi-recv: texto demasiado grande "
                            f"({fsize} bytes > 1 MB) de {addr[0]}")
                      return
                  data = remaining
                  while len(data) < fsize:
                      chunk = conn.recv(min(65536, fsize - len(data)))
                      if not chunk:
                          break
                      data += chunk
                  text = data[:fsize].decode('utf-8', errors='replace')
                  print(f"+ Texto recibido de {addr[0]}: {text}")

          except Exception as e:
              print(f"Error wifi-recv (conexion de {addr[0]}): {e}")
              if save_path and os.path.exists(save_path):
                  try:
                      os.remove(save_path)
                  except Exception:
                      pass
          finally:
              try:
                  conn.close()
              except Exception:
                  pass

      while True:
          # Comprueba kill signal sin bloquear
          try:
              msg = forth._actor_queue.get_nowait()
              if _KS is not None and msg is _KS:
                  break
              forth._actor_queue.put(msg)
          except _qmod.Empty:
              pass
          except Exception:
              break

          # accept() expira cada 1 s (settimeout), vuelve a comprobar kill
          try:
              conn, addr = srv.accept()
              threading.Thread(target=_handle,
                               args=(conn, addr),
                               daemon=True).start()
          except socket.timeout:
              continue
          except OSError:
              break

      try:
          srv.close()
      except Exception:
          pass
      print("+ wifi-recv detenido")
  }py ;


: wifi-recv-start  ( -- )
  wifi-recv-actor @ 0<> if
    ." wifi-recv ya esta activo (usa wifi-recv-stop primero)" cr exit
  then
  s" _wifi-recv-body" actor-spawn
  dup wifi-recv-actor !
  actor-run
  \ Espera breve; si el actor murio de inmediato (puerto ocupado) limpia el id
  py{
  import time
  time.sleep(0.4)
  try:
      from pfforth.actors import ForthActors
      aid = int(forth.variables.get('wifi-recv-actor', 0))
      if aid:
          with ForthActors._registry_lock:
              entry = ForthActors._registry.get(aid)
          if entry and not entry.get('alive', False) and not entry.get('pending', False):
              forth.variables['wifi-recv-actor'] = 0
              print("(actor detenido — reintenta con otro puerto o revisa el error)")
  except Exception:
      pass
  }py ;


: wifi-recv-stop  ( -- )
  wifi-recv-actor @ dup 0= if
    drop ." wifi-recv no esta activo" cr exit
  then
  actor-kill
  0 wifi-recv-actor ! ;
