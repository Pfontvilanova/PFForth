# FORTH CODE WORD: code/camera/campreview
# Muestra el stream en vivo en una ventana (bloquea hasta cerrar)

WORD_NAME = 'cam-preview'
# === STACK EFFECT ===
# ( -- )  Abre ventana y muestra el stream hasta que el usuario cierra
#         o pulsa 'q'.  En iPad/headless: servidor HTTP en localhost:8765
#         Safari se conecta a esa URL; el stream espera la conexion.
# === FIN ===

import os
import sys
import select
import time


def _load_h(caller_file):
    key = '_cam_helper'
    if key in sys.modules:
        return sys.modules[key]
    import importlib.util
    here  = os.path.dirname(os.path.abspath(caller_file))
    fpath = os.path.join(here, '_cam.py')
    spec  = importlib.util.spec_from_file_location(key, fpath)
    mod   = importlib.util.module_from_spec(spec)
    sys.modules[key] = mod
    spec.loader.exec_module(mod)
    return mod


def _video_fps(cap):
    """Devuelve FPS del video (entre 5 y 60). Si falla, 25."""
    import cv2
    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps and 5 <= fps <= 120:
        return fps
    return 25.0


def _is_video_file(cam):
    """True si la fuente es un archivo de video (no camara en vivo)."""
    src = cam.get('source', '')
    if not isinstance(src, str):
        return False
    return any(src.lower().endswith(ext)
               for ext in ('.mp4', '.avi', '.mkv', '.mov', '.m4v', '.webm'))


def execute(forth):
    h   = _load_h(__file__)
    cam = h._ensure_cam(forth)

    if cam['cap'] is None:
        print("Error: no hay camara abierta — usa cam-open primero")
        return

    try:
        import cv2
    except ImportError:
        print("Error: opencv-python no instalado — pip install opencv-python")
        return

    use_display = h._has_display()
    is_video    = _is_video_file(cam)
    fps         = _video_fps(cam['cap'])
    frame_delay = 1.0 / fps           # segundos entre frames

    if use_display:
        win = cam['window_name']
        cv2.namedWindow(win, cv2.WINDOW_NORMAL)
        cam['window_open'] = True
        print("Streaming activo — pulsa 'q' o cierra la ventana para salir")
    else:
        port = cam.get('mjpeg_port', 8765)
        # Reiniciar siempre el servidor para evitar conexiones colgadas
        if cam.get('mjpeg_running'):
            h._stop_mjpeg_server(forth)
            time.sleep(0.3)
        srv = h._start_mjpeg_server(forth, port)
        if srv is None:
            return
        print(f"Abre esta URL en Safari:")
        print(f"  http://127.0.0.1:{port}")
        print(f"  (pulsa q + Enter aqui para detener)")

    # --- Hilo para detectar 'q' sin bloquear el bucle principal ---
    import threading
    quit_event = threading.Event()

    def _wait_for_q():
        try:
            while not quit_event.is_set():
                line = sys.stdin.readline()
                if 'q' in line.lower():
                    quit_event.set()
                    break
        except Exception:
            quit_event.set()

    if not use_display:
        q_thread = threading.Thread(target=_wait_for_q, daemon=True)
        q_thread.start()

    try:
        loop_count = 0
        while True:
            if not use_display and quit_event.is_set():
                break

            t0 = time.time()
            ret, frame = cam['cap'].read()

            if not ret:
                if is_video:
                    loop_count += 1
                    cam['cap'].set(cv2.CAP_PROP_POS_FRAMES, 0)
                    ret, frame = cam['cap'].read()
                    if not ret:
                        print("+ Fin del video (no se puede releer)")
                        break
                    if loop_count == 1:
                        print()
                        print("+ Video terminado, reproduciendo desde el inicio")
                        print("  (pulsa q + Enter para detener)")
                else:
                    print("+ Camara desconectada")
                    break

            cam['frame']            = frame
            forth._ai['image']      = h._frame_to_pil(frame)
            forth._ai['detections'] = None

            det  = forth._ai.get('detections')
            disp = h._draw_detections(frame, det) if det else frame

            if use_display:
                cv2.imshow(cam['window_name'], disp)
                wait_ms = max(1, int(frame_delay * 1000))
                key = cv2.waitKey(wait_ms) & 0xFF
                if key == ord('q'):
                    break
                try:
                    if cv2.getWindowProperty(cam['window_name'],
                                             cv2.WND_PROP_VISIBLE) < 1:
                        break
                except Exception:
                    break
            else:
                elapsed = time.time() - t0
                sleep_t = frame_delay - elapsed
                if sleep_t > 0:
                    time.sleep(sleep_t)

    except KeyboardInterrupt:
        pass
    finally:
        quit_event.set()   # detiene el hilo lector si sigue activo
        if use_display:
            try:
                cv2.destroyWindow(cam['window_name'])
            except Exception:
                pass
            cam['window_open'] = False
        else:
            h._stop_mjpeg_server(forth)
        print("+ Preview detenido")
