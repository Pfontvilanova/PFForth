# FORTH CODE WORD: code/wifi/myip
# Get local IP address

WORD_NAME = 'my-ip'
#
# === CÓDIGO FORTH ORIGINAL ===
# ( -- ip ) Get local IP address
# === FIN CÓDIGO FORTH ===

import socket

def execute(forth):
    def push(val):
        forth.stack.append(val)
    
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        push(ip)
    except Exception as e:
        push("127.0.0.1")
