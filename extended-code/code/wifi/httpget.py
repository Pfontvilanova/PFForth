# FORTH CODE WORD: code/wifi/httpget
# HTTP GET request

WORD_NAME = 'http-get'
#
# === CÓDIGO FORTH ORIGINAL ===
# ( url -- response ) Perform HTTP GET, return response object
# === FIN CÓDIGO FORTH ===

import requests

def execute(forth):
    def push(val):
        forth.stack.append(val)
    def pop():
        if not forth.stack:
            raise IndexError("Stack underflow")
        return forth.stack.pop()
    
    if len(forth.stack) < 1:
        print("Error: HTTP-GET requiere URL")
        return
    
    url = str(pop())
    
    try:
        resp = requests.get(url, timeout=10)
        push(resp)
    except Exception as e:
        print(f"Error HTTP-GET: {e}")
        push(None)
