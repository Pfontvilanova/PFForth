# FORTH CODE WORD: code/wifi/mqttloop
# Process MQTT messages (non-blocking)

WORD_NAME = 'mqtt-loop'
#
# === CÓDIGO FORTH ORIGINAL ===
# ( client -- client ) Process pending MQTT messages
# === FIN CÓDIGO FORTH ===

def execute(forth):
    def push(val):
        forth.stack.append(val)
    def pop():
        if not forth.stack:
            raise IndexError("Stack underflow")
        return forth.stack.pop()
    
    if len(forth.stack) < 1:
        print("Error: MQTT-LOOP requiere client")
        return
    
    client = pop()
    
    try:
        if client:
            client.loop(timeout=0.1)
        push(client)
    except Exception as e:
        print(f"Error MQTT loop: {e}")
        push(client)
