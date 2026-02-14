# FORTH CODE WORD: code/wifi/resolve
# DNS resolution

WORD_NAME = 'resolve'
#
# === CÓDIGO FORTH ORIGINAL ===
# ( hostname -- ip ) Resolve hostname to IP address
# === FIN CÓDIGO FORTH ===

import socket

def execute(forth):
    def push(val):
        forth.stack.append(val)
    def pop():
        if not forth.stack:
            raise IndexError("Stack underflow")
        return forth.stack.pop()
    
    if len(forth.stack) < 1:
        print("Error: RESOLVE requiere hostname")
        return
    
    hostname = str(pop())
    
    try:
        ip = socket.gethostbyname(hostname)
        push(ip)
    except Exception as e:
        print(f"Error resolve: {e}")
        push("")
