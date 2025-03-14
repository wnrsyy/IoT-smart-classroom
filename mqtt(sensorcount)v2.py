# Using uasyncio for Asynchronous Execution
import uasyncio as asyncio
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
async def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect('666wifipassword', '1133335678')
    while not wlan.isconnected():
        await asyncio.sleep(1)
    print('Connected to Wi-Fi, IP address:', wlan.ifconfig()[0])

# Connect to MQTT broker
async def connect_mqtt():
    global client
    try:
        client = MQTTClient(mqtt_client_id, mqtt_broker, port=1883)
        client.connect(clean_session=False)
        client.set_last_will(sensor_topic, "Disconnected")
        print("Connected to MQTT broker")
    except OSError as e:
        print("Failed to connect to MQTT broker:", e)

# Disconnect from MQTT broker
async def disconnect_mqtt():
    global client
    if client:
        try:
            client.disconnect()
            print("Disconnected from MQTT broker")
        except OSError as e:
            print("Error disconnecting MQTT:", e)

# Reading data from DHT22 and ESP32 sensor
async def reading_sensor():
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
async def check_pir():
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
        await asyncio.sleep(1)

# Main async function
async def main():
    print("Waiting For Power On Warm Up")
    await asyncio.sleep(3)
    print("Ready!")

    # Connect to Wi-Fi and MQTT
    await connect_wifi()
    await connect_mqtt()

    # Run sensor reading and PIR checking concurrently
    asyncio.create_task(reading_sensor())
    await check_pir()

# Run the asyncio event loop
try:
    asyncio.run(main())
except KeyboardInterrupt:
    print("Disconnected from MQTT broker.")
    asyncio.run(disconnect_mqtt())
