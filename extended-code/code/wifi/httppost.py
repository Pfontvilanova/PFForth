# FORTH CODE WORD: code/wifi/httppost
# HTTP POST request

WORD_NAME = 'http-post'
#
# === CÓDIGO FORTH ORIGINAL ===
# ( url data -- response ) Perform HTTP POST with data
# === FIN CÓDIGO FORTH ===

import requests

def execute(forth):
    def push(val):
        forth.stack.append(val)
    def pop():
        if not forth.stack:
            raise IndexError("Stack underflow")
        return forth.stack.pop()
    
    if len(forth.stack) < 2:
        print("Error: HTTP-POST requiere (url data)")
        return
    
    data = pop()
    url = str(pop())
    
    try:
        if isinstance(data, dict):
            resp = requests.post(url, json=data, timeout=10)
        else:
            resp = requests.post(url, data=str(data), timeout=10)
        push(resp)
    except Exception as e:
        print(f"Error HTTP-POST: {e}")
        push(None)
