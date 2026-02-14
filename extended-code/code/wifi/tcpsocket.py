# FORTH CODE WORD: code/wifi/tcpsocket
# Create a TCP socket

WORD_NAME = 'tcp-socket'
#
# === CÓDIGO FORTH ORIGINAL ===
# ( -- sock ) Create a TCP socket and push to stack
# === FIN CÓDIGO FORTH ===

import socket

def execute(forth):
    def push(val):
        forth.stack.append(val)
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        push(sock)
    except Exception as e:
        print(f"Error: {e}")
        push(0)
