# FORTH CODE WORD: code/wifi/mqttdisconnect
# Disconnect from MQTT broker

WORD_NAME = 'mqtt-disconnect'
#
# === CÓDIGO FORTH ORIGINAL ===
# ( client -- ) Disconnect from MQTT broker
# === FIN CÓDIGO FORTH ===

def execute(forth):
    def pop():
        if not forth.stack:
            raise IndexError("Stack underflow")
        return forth.stack.pop()
    
    if len(forth.stack) < 1:
        print("Error: MQTT-DISCONNECT requiere client")
        return
    
    client = pop()
    
    try:
        if client:
            client.loop_stop()
            client.disconnect()
            print("MQTT desconectado")
    except Exception as e:
        print(f"Error MQTT disconnect: {e}")
