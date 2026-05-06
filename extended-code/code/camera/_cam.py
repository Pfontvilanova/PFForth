"""
Helper compartido para el vocabulario de cámara.
No es una palabra Forth — empieza con _ para que IMPORT code/camera lo ignore.
"""

import os
import sys
import platform


def _ensure_cam(forth):
    if not hasattr(forth, '_cam'):
        forth._cam = {}
    cam = forth._cam
    defaults = {
        'cap':           None,
        'frame':         None,
        'source':        None,
        'bg_sub':        None,
        'zone':          None,
        'window_name':   'pfforth-cam',
        'window_open':   False,
        'mjpeg_running': False,
        'mjpeg_server':  None,
        'mjpeg_thread':  None,
        'mjpeg_port':    8765,
    }
    for k, v in defaults.items():
        cam.setdefault(k, v)
    if not hasattr(forth, '_ai'):
        forth._ai = {}
    forth._ai.setdefault('image', None)
    forth._ai.setdefault('detections', None)
    return cam


def _has_display():
    if platform.system() == 'Darwin':
        if os.environ.get('TERM_PROGRAM', '') == 'a-Shell':
            return False
        return True
    return bool(os.environ.get('DISPLAY') or os.environ.get('WAYLAND_DISPLAY'))


def _frame_to_pil(frame):
    from PIL import Image
    rgb = frame[:, :, ::-1].copy()
    return Image.fromarray(rgb)


def _draw_detections(frame, detections):
    import cv2
    if not detections:
        return frame
    out = frame.copy()
    for d in detections:
        x1, y1, x2, y2 = [int(v) for v in d['box']]
        label = d['label']
        conf  = d['conf']
        color = (0, 220, 0) if label == 'person' else (255, 140, 0)
        cv2.rectangle(out, (x1, y1), (x2, y2), color, 2)
        txt = f"{label} {conf:.2f}"
        (tw, th), _ = cv2.getTextSize(txt, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
        y_bg = max(y1 - th - 6, 0)
        cv2.rectangle(out, (x1, y_bg), (x1 + tw + 4, y_bg + th + 6), color, -1)
        cv2.putText(out, txt, (x1 + 2, y_bg + th + 2),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)
    return out


_HTML_PAGE = b"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>pfforth cam</title>
  <style>
    body { margin:0; background:#000; display:flex;
           justify-content:center; align-items:center; height:100vh; }
    img  { max-width:100%; max-height:100vh; display:block; }
    #info { position:fixed; top:8px; left:8px; color:#0f0;
            font:14px monospace; background:rgba(0,0,0,.5);
            padding:4px 8px; border-radius:4px; }
  </style>
</head>
<body>
  <img id="cam" src="/frame.jpg">
  <div id="info">pfforth cam</div>
  <script>
    var fps = 0, last = Date.now(), frames = 0;
    function refresh() {
      var img = new Image();
      img.onload = function() {
        document.getElementById('cam').src = img.src;
        frames++;
        var now = Date.now();
        if (now - last >= 1000) {
          fps = frames; frames = 0; last = now;
          document.getElementById('info').textContent = 'pfforth cam  ' + fps + ' fps';
        }
        setTimeout(refresh, 80);
      };
      img.onerror = function() { setTimeout(refresh, 500); };
      img.src = '/frame.jpg?' + Date.now();
    }
    refresh();
  </script>
</body>
</html>"""


def _get_local_ip():
    """Devuelve la IP local real del equipo (no 127.0.0.1).
    Usa un socket UDP efímero a 8.8.8.8:80 — no envía datos."""
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return '127.0.0.1'


def _start_mjpeg_server(forth, port=8765, on_connect=None, on_disconnect=None):
    import threading
    from http.server import BaseHTTPRequestHandler, HTTPServer
    import time

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            try:
                self._handle()
            except BrokenPipeError:
                if on_disconnect:
                    on_disconnect(self.client_address)
            except ConnectionResetError:
                if on_disconnect:
                    on_disconnect(self.client_address)
            except Exception:
                pass

        def _handle(self):
            if self.path == '/' or self.path == '/index.html':
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.send_header('Content-Length', str(len(_HTML_PAGE)))
                self.end_headers()
                self.wfile.write(_HTML_PAGE)

            elif self.path.startswith('/frame.jpg'):
                frame = forth._cam.get('frame')
                if frame is None:
                    self.send_response(503)
                    self.end_headers()
                    return
                import cv2
                det  = getattr(forth, '_ai', {}).get('detections')
                disp = _draw_detections(frame, det) if det else frame
                _, jpg = cv2.imencode('.jpg', disp,
                                     [cv2.IMWRITE_JPEG_QUALITY, 80])
                data = jpg.tobytes()
                self.send_response(200)
                self.send_header('Content-Type', 'image/jpeg')
                self.send_header('Content-Length', str(len(data)))
                self.send_header('Cache-Control', 'no-store')
                self.end_headers()
                if on_connect:
                    on_connect(self.client_address)
                self.wfile.write(data)

            else:
                self.send_response(404)
                self.end_headers()

        def log_message(self, *a):
            pass

        def log_error(self, *a):
            pass

    class QuietHTTPServer(HTTPServer):
        allow_reuse_address = True

        def handle_error(self, request, client_address):
            import sys
            exc = sys.exc_info()[1]
            if isinstance(exc, (BrokenPipeError, ConnectionResetError)):
                return
            super().handle_error(request, client_address)

    try:
        server = QuietHTTPServer(('0.0.0.0', port), Handler)
    except OSError as e:
        print(f"Error: no se pudo iniciar servidor en puerto {port}: {e}")
        print(f"  Espera unos segundos y vuelve a intentarlo, o usa otro puerto:")
        print(f"  {port + 1} wifi-stream-port !   video-stream-start")
        return None

    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    time.sleep(0.3)

    forth._cam['mjpeg_running'] = True
    forth._cam['mjpeg_server']  = server
    forth._cam['mjpeg_thread']  = t
    return server


def _stop_mjpeg_server(forth):
    cam = getattr(forth, '_cam', {})
    cam['mjpeg_running'] = False
    srv = cam.get('mjpeg_server')
    if srv:
        try:
            srv.shutdown()
        except Exception:
            pass
        try:
            srv.server_close()
        except Exception:
            pass
        cam['mjpeg_server'] = None
        cam['mjpeg_thread'] = None


def _helper_loader(file_in_camera_dir):
    """Devuelve el módulo _cam cargado; file_in_camera_dir = __file__ del caller."""
    key = '_cam_helper'
    if key in sys.modules:
        return sys.modules[key]
    here  = os.path.dirname(os.path.abspath(file_in_camera_dir))
    fpath = os.path.join(here, '_cam.py')
    import importlib.util
    spec = importlib.util.spec_from_file_location(key, fpath)
    mod  = importlib.util.module_from_spec(spec)
    sys.modules[key] = mod
    spec.loader.exec_module(mod)
    return mod
