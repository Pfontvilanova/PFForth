# FORTH CODE WORD: code/wifi/wificonnect
# Connect to configured WiFi network

WORD_NAME = 'wifi-connect'
#
# === CÓDIGO FORTH ORIGINAL ===
# ( -- flag ) Connect to WiFi, returns -1 success, 0 fail
# === FIN CÓDIGO FORTH ===

def execute(forth):
    def push(val):
        forth.stack.append(val)
    
    if not hasattr(forth, 'wifi_config') or 'ssid' not in forth.wifi_config:
        print("Error: Primero usa WIFI-CONFIG con SSID y password")
        push(0)
        return
    
    ssid = forth.wifi_config['ssid']
    password = forth.wifi_config['password']
    
    try:
        import network
        wlan = network.WLAN(network.STA_IF)
        wlan.active(True)
        if not wlan.isconnected():
            print(f"Conectando a {ssid}...")
            wlan.connect(ssid, password)
            import time
            timeout = 10
            while not wlan.isconnected() and timeout > 0:
                time.sleep(1)
                timeout -= 1
        
        if wlan.isconnected():
            print(f"Conectado! IP: {wlan.ifconfig()[0]}")
            push(-1)
        else:
            print("Error: Timeout de conexion")
            push(0)
    except ImportError:
        print(f"PC/Servidor: WiFi gestionado por SO")
        print(f"Credenciales guardadas: {ssid}")
        push(-1)
    except Exception as e:
        print(f"Error WiFi: {e}")
        push(0)
