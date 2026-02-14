# FORTH CODE WORD: code/wifi/netinfo
# Display network information

WORD_NAME = 'net-info'
#
# === CÓDIGO FORTH ORIGINAL ===
# ( -- ) Display network information
# === FIN CÓDIGO FORTH ===

import socket

def execute(forth):
    try:
        hostname = socket.gethostname()
        print(f"Hostname: {hostname}")
        
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            print(f"Local IP: {local_ip}")
        except:
            print("Local IP: (no disponible)")
        
        try:
            external_ip = socket.gethostbyname(hostname)
            print(f"External: {external_ip}")
        except:
            pass
            
    except Exception as e:
        print(f"Error: {e}")
