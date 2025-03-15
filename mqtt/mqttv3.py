# Improved Blocking Code with Better Error Handling (Structured Approach)
import time
from machine import Pin
from umqtt.simple import MQTTClient
import dht
import json
import esp32
import gc
import network

gc.collect()

# Setting GPIO Pins for DHT22 and PIR sensor
sensor = dht.DHT22(Pin(16))
pir_sensor = Pin(23, Pin.IN)

# MQTT Configuration
mqtt_broker = "192.168.43.212"
mqtt_client_id = "esp32-sensor"
sensor_topic = "sensor_data"
client = None

# Wi-Fi Connection
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect('666wifipassword', '1133335678')
    timeout = 10
    while not wlan.isconnected() and timeout > 0:
        time.sleep(1)
        timeout -= 1
    if wlan.isconnected():
        print('Connected to Wi-Fi:', wlan.ifconfig()[0])
    else:
        print("Failed to connect to Wi-Fi. Restarting...")
        machine.reset()

# MQTT Connection
def connect_mqtt():
    global client
    try:
        client = MQTTClient(mqtt_client_id, mqtt_broker, port=1883)
        client.connect(clean_session=False)
        client.set_last_will(sensor_topic, "Disconnected")
        print("Connected to MQTT broker")
    except OSError as e:
        print(f"Failed to connect to MQTT broker: {e}")
        time.sleep(5)
        connect_mqtt()

# Disconnect from MQTT
def disconnect_mqtt():
    global client
    if client:
        try:
            client.disconnect()
            print("Disconnected from MQTT broker")
        except OSError as e:
            print(f"Error disconnecting MQTT: {e}")

# Reading Sensor Data
def reading_sensor():
    try:
        sensor.measure()
        temperature = sensor.temperature()
        humidity = sensor.humidity()
        temperature_esp32 = (esp32.raw_temperature() - 32.0) / 1.8
        print(f"Temperature (DHT): {temperature}C, Humidity (DHT): {humidity}%, Temperature (ESP32): {temperature_esp32}C")
        
        data = {
            "temperature": temperature,
            "humidity": humidity,
            "esp32_temperature": temperature_esp32
        }

        payload = json.dumps(data)
        if client:
            print(f"Publishing to MQTT: {payload}")
            client.publish(sensor_topic, payload)
        else:
            print("MQTT client not connected!")

    except Exception as e:
        print(f"Error reading sensor: {e}")

# PIR Motion Detection
def check_pir():
    warm_up = 0
    while True:
        sensor_output = pir_sensor.value()
        if sensor_output == 0:
            if warm_up == 1:
                warm_up = 0
            print("Nobody here (--!)\n")
        else:
            print("I'm here!\n")
            warm_up = 1
        time.sleep(1)

# Main Function
def main():
    print("Waiting For Power On Warm Up")
    time.sleep(5)  # Power On Warm Up Delay
    print("Ready!")

    # Connect to Wi-Fi and MQTT
    connect_wifi()
    connect_mqtt()

    try:
        while True:
            reading_sensor()
            check_pir()
            time.sleep(1)
    except KeyboardInterrupt:
        print("Disconnected from Broker")
        disconnect_mqtt()

if __name__ == "__main__":
    main()
