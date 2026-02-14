# FORTH CODE WORD: code/wifi/mqttsubscribe
# Subscribe to MQTT topic

WORD_NAME = 'mqtt-subscribe'
#
# === CÓDIGO FORTH ORIGINAL ===
# ( client topic -- client ) Subscribe to topic
# === FIN CÓDIGO FORTH ===

def execute(forth):
    def push(val):
        forth.stack.append(val)
    def pop():
        if not forth.stack:
            raise IndexError("Stack underflow")
        return forth.stack.pop()
    
    if len(forth.stack) < 2:
        print("Error: MQTT-SUBSCRIBE requiere (client topic)")
        return
    
    topic = str(pop())
    client = pop()
    
    try:
        if client:
            client.subscribe(topic)
            print(f"Suscrito a {topic}")
        push(client)
    except Exception as e:
        print(f"Error MQTT subscribe: {e}")
        push(client)
