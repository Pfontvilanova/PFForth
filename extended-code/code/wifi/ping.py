# FORTH CODE WORD: code/wifi/ping
# Simple ping (TCP connect timing)

WORD_NAME = 'ping'
#
# === CÓDIGO FORTH ORIGINAL ===
# ( addr port -- ms ) Measure TCP connect time in milliseconds
# === FIN CÓDIGO FORTH ===

import socket
import time

def execute(forth):
    def push(val):
        forth.stack.append(val)
    def pop():
        if not forth.stack:
            raise IndexError("Stack underflow")
        return forth.stack.pop()
    
    if len(forth.stack) < 2:
        print("Error: PING requiere (addr port)")
        return
    
    port = int(pop())
    addr = str(pop())
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        
        start = time.time()
        sock.connect((addr, port))
        end = time.time()
        sock.close()
        
        ms = int((end - start) * 1000)
        push(ms)
    except Exception as e:
        print(f"Error ping: {e}")
        push(-1)
