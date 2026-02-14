# FORTH CODE WORD: code/wifi/wifistatus
# Show WiFi connection status

WORD_NAME = 'wifi-status'
#
# === CÓDIGO FORTH ORIGINAL ===
# ( -- ) Display WiFi connection status
# === FIN CÓDIGO FORTH ===

def execute(forth):
    try:
        import network
        wlan = network.WLAN(network.STA_IF)
        if wlan.isconnected():
            config = wlan.ifconfig()
            print(f"Estado: Conectado")
            print(f"IP: {config[0]}")
            print(f"Mascara: {config[1]}")
            print(f"Gateway: {config[2]}")
            print(f"DNS: {config[3]}")
            try:
                print(f"RSSI: {wlan.status('rssi')} dBm")
            except:
                pass
        else:
            print("Estado: Desconectado")
    except ImportError:
        import socket
        try:
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            print(f"Plataforma: PC/Servidor")
            print(f"Hostname: {hostname}")
            print(f"IP Local: {local_ip}")
            if hasattr(forth, 'wifi_config') and 'ssid' in forth.wifi_config:
                print(f"SSID configurado: {forth.wifi_config['ssid']}")
            else:
                print("Sin credenciales WiFi configuradas")
        except Exception as e:
            print(f"Error obteniendo info: {e}")
    except Exception as e:
        print(f"Error: {e}")
