# FORTH CODE WORD: code/wifi/udpsocket
# Create a UDP socket

WORD_NAME = 'udp-socket'
#
# === CÓDIGO FORTH ORIGINAL ===
# ( -- sock ) Create a UDP socket and push to stack
# === FIN CÓDIGO FORTH ===

import socket

def execute(forth):
    def push(val):
        forth.stack.append(val)
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        push(sock)
    except Exception as e:
        print(f"Error: {e}")
        push(0)
