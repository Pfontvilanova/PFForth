# FORTH CODE WORD: code/wifi/httppostfile
# HTTP POST a file as binary body (useful for ntfy.sh attachments, etc.)

WORD_NAME = 'http-post-file'
#
# === CÓDIGO FORTH ORIGINAL ===
# ( url path -- response )
# Llegeix el fitxer 'path' i el puja via HTTP POST com a cos binari.
# Afegeix la capcelera Filename amb el nom del fitxer.
# Exemple: s" https://ntfy.sh/topic" s" foto2.jpeg" http-post-file
# === FIN CÓDIGO FORTH ===

import requests
import os

def execute(forth):
    if len(forth.stack) < 2:
        print("Error: http-post-file requiere (url path)")
        return
    path = str(forth.stack.pop())
    url  = str(forth.stack.pop())
    fname = os.path.basename(path)
    try:
        with open(path, 'rb') as f:
            resp = requests.post(
                url,
                data=f,
                headers={
                    'Filename':     fname,
                    'Content-Type': 'application/octet-stream',
                },
                timeout=30,
            )
        forth.stack.append(resp)
    except FileNotFoundError:
        print(f"Error http-post-file: fitxer no trobat: {path}")
        forth.stack.append(None)
    except Exception as e:
        print(f"Error http-post-file: {e}")
        forth.stack.append(None)
