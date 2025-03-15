# Refined Blocking Code with Improved Error Handling and Comments
# No need for multiple except blocks unless necessary.
import time
from machine import Pin
from umqtt.simple import MQTTClient
import json
import network
import gc

gc.collect()

# Pin Definitions
PIR_SENSOR_1_PIN = 23
PIR_SENSOR_2_PIN = 16
pir_sensor_1 = Pin(PIR_SENSOR_1_PIN, Pin.IN)
pir_sensor_2 = Pin(PIR_SENSOR_2_PIN, Pin.IN)

# MQTT Configuration
mqtt_broker = "192.168.43.212"
mqtt_client_id = "esp32-sensor"
sensor_topic = "sensor_data"

client = None

# Wi-Fi Connection Setup
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect('666wifipassword', '1133335678')
    while not wlan.isconnected():
        time.sleep(1)
    print('Connected to Wi-Fi, IP address:', wlan.ifconfig()[0])

# MQTT Connection Setup
def connect_mqtt():
    global client
    try:
        client = MQTTClient(mqtt_client_id, mqtt_broker, port=1883)
        client.connect(clean_session=False)
        client.set_last_will(sensor_topic, "Disconnected")
        print("Connected to MQTT broker")
    except OSError as e:
        print("Failed to connect to MQTT broker:", e)

# Disconnect MQTT
def disconnect_mqtt():
    global client
    if client:
        try:
            client.disconnect()
            print("Disconnected from MQTT broker")
        except OSError as e:
            print("Error disconnecting MQTT:", e)

# PIR Sensor Check
def check_pir():
    last_triggered = None
    while True:
        sensor_1_state = pir_sensor_1.value()
        sensor_2_state = pir_sensor_2.value()

        if sensor_1_state and not sensor_2_state:
            last_triggered = "sensor_1"
        elif sensor_2_state and not sensor_1_state:
            last_triggered = "sensor_2"
        elif sensor_1_state and sensor_2_state:
            if last_triggered == "sensor_1":
                print("คนเดินเข้า")
                if client:
                    client.publish(sensor_topic, json.dumps({"motion": "in"}))
            elif last_triggered == "sensor_2":
                print("คนเดินออก")
                if client:
                    client.publish(sensor_topic, json.dumps({"motion": "out"}))
            last_triggered = None
        time.sleep(0.5)

# Main Loop
def main():
    print("Waiting For Power On Warm Up")
    time.sleep(3)
    print("Ready!")

    # Connect Wi-Fi and MQTT
    connect_wifi()
    connect_mqtt()

    # PIR sensor checking loop
    try:
        check_pir()
    except KeyboardInterrupt:
        print("Disconnected from MQTT broker.")
        disconnect_mqtt()

if __name__ == "__main__":
    main()
