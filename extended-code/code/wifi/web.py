# FORTH CODE WORD: code/wifi/web
# Open a URL in the system default web browser (stream interface)

WORD_NAME = '>web'
#
# === CÓDIGO FORTH ORIGINAL ===
# ( -- obj ) Crea un stream de salida que abre URLs en el navegador.
# Uso:
#   >web output-to
#   s" ejemplo.com" type cr    \ cr dispara la apertura
#   output-to-console
# Compatible con a-Shell (iOS) y escritorio.
# === FIN CÓDIGO FORTH ===


def _open_url(url):
    """Abre una URL usando el método adecuado según la plataforma."""
    import sys
    import subprocess

    url = url.strip()
    if not url:
        return
    if not url.startswith('http'):
        url = 'https://' + url

    print(f"Abriendo: {url}")

    # a-Shell / iOS
    if sys.platform == 'ios' or _is_ashell():
        try:
            subprocess.run(['open', url], check=False)
            return
        except Exception:
            pass

    # macOS
    if sys.platform == 'darwin':
        try:
            subprocess.run(['open', url], check=False)
            return
        except Exception:
            pass

    # Linux
    if sys.platform.startswith('linux'):
        for cmd in ['xdg-open', 'sensible-browser', 'x-www-browser']:
            try:
                subprocess.run([cmd, url], check=False)
                return
            except FileNotFoundError:
                continue

    # Windows
    if sys.platform == 'win32':
        try:
            subprocess.run(['start', url], shell=True, check=False)
            return
        except Exception:
            pass

    # Fallback genérico
    try:
        import webbrowser
        webbrowser.open(url)
    except Exception as e:
        print(f"Error al abrir navegador: {e}")


def _is_ashell():
    import os
    if os.environ.get('TERM_PROGRAM') == 'a-Shell':
        return True
    if os.path.exists('/var/mobile') or os.path.exists('/private/var/mobile'):
        return True
    return False


def execute(forth):
    forth_ref = forth

    class _WebBrowserOutput:
        def __init__(self):
            self._buf = ''

        def write(self, s):
            self._buf += s
            if '\n' in self._buf:
                parts = self._buf.split('\n')
                for url in parts[:-1]:
                    _open_url(url)
                self._buf = parts[-1]

        def flush(self):
            if self._buf.strip():
                _open_url(self._buf)
                self._buf = ''

    forth.stack.append(_WebBrowserOutput())
