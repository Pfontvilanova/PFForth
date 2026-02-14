# FORTH CODE WORD: code/wifi/wificonfig
# Configure WiFi credentials

WORD_NAME = 'wifi-config'
#
# === CÓDIGO FORTH ORIGINAL ===
# ( ssid password -- ) Store WiFi credentials for connection
# === FIN CÓDIGO FORTH ===

def execute(forth):
    def pop():
        if not forth.stack:
            raise IndexError("Stack underflow")
        return forth.stack.pop()
    
    if len(forth.stack) < 2:
        print("Error: WIFI-CONFIG requiere SSID y password")
        return
    
    password = str(pop())
    ssid = str(pop())
    
    if not hasattr(forth, 'wifi_config'):
        forth.wifi_config = {}
    
    forth.wifi_config['ssid'] = ssid
    forth.wifi_config['password'] = password
    
    print(f"WiFi configurado: {ssid}")
