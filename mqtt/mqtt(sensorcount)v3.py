# Improved Blocking Code with Better Error Handling
import time
from machine import Pin
from umqtt.simple import MQTTClient
import dht
import json
import esp32
import gc
import network

gc.collect()

# Pin setup for DHT22 and PIR sensor
sensor = dht.DHT22(Pin(16))
pir_sensor = Pin(23, Pin.IN)

# MQTT Configuration
mqtt_broker = "192.168.43.212"
mqtt_client_id = "esp32-sensor"
sensor_topic = "sensor_data"

client = None

# Connect to Wi-Fi
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect('666wifipassword', '1133335678')
    while not wlan.isconnected():
        time.sleep(1)
    print('Connected to Wi-Fi, IP address:', wlan.ifconfig()[0])

# Connect to MQTT broker
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

# Disconnect from MQTT broker
def disconnect_mqtt():
    global client
    if client:
        try:
            client.disconnect()
            print("Disconnected from MQTT broker")
        except OSError as e:
            print(f"Error disconnecting MQTT: {e}")

# Reading data from DHT22 and ESP32 sensor
def reading_sensor():
    try:
        sensor.measure()
        temperature_dht = sensor.temperature()
        humidity_dht = sensor.humidity()
        temperature_esp32 = (esp32.raw_temperature() - 32.0) / 1.8
        print(f"Temperature (DHT): {temperature_dht}°C, Humidity (DHT): {humidity_dht}%, Temperature (ESP32): {temperature_esp32:.2f}°C")
        
        payload = {
            'temperature': temperature_dht,
            'humidity': humidity_dht,
            'esp32Temperature': temperature_esp32
        }
        if client:
            client.publish(sensor_topic, json.dumps(payload))
    except OSError:
        print("Error reading sensor.")

# PIR motion detection
def check_pir():
    had_object = False
    counter = 0
    warm_up = False
    while True:
        sensor_output = pir_sensor.value()
        if sensor_output == 0 or had_object:
            had_object = False
            if warm_up:
                warm_up = False
        else:
            counter += 1
            print(f"Motion detected, counter: {counter}")
            had_object = True
            warm_up = True
        time.sleep(1)

# Main loop
def main():
    print("Waiting For Power On Warm Up")
    time.sleep(3)
    print("Ready!")

    # Connect to Wi-Fi and MQTT
    connect_wifi()
    connect_mqtt()

    try:
        while True:
            reading_sensor()
            check_pir()
    except KeyboardInterrupt:
        print("Disconnected from MQTT broker.")
        disconnect_mqtt()

if __name__ == "__main__":
    main()
