# FORTH CODE WORD: code/wifi/mqttpublish
# Publish message to MQTT topic

WORD_NAME = 'mqtt-publish'
#
# === CÓDIGO FORTH ORIGINAL ===
# ( client topic msg -- client ) Publish message to topic
# === FIN CÓDIGO FORTH ===

def execute(forth):
    def push(val):
        forth.stack.append(val)
    def pop():
        if not forth.stack:
            raise IndexError("Stack underflow")
        return forth.stack.pop()
    
    if len(forth.stack) < 3:
        print("Error: MQTT-PUBLISH requiere (client topic msg)")
        return
    
    msg = str(pop())
    topic = str(pop())
    client = pop()
    
    try:
        if client:
            client.publish(topic, msg)
            print(f"Publicado en {topic}")
        push(client)
    except Exception as e:
        print(f"Error MQTT publish: {e}")
        push(client)
