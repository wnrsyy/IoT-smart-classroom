# Using uasyncio for Asynchronous Execution (Non-blocking)
import uasyncio as asyncio
from machine import Pin
from umqtt.simple import MQTTClient
import time
import esp32
import dht
import gc
import json
import network

gc.collect()

# Setting up GPIO Pins for DHT22 and PIR sensor
sensor = dht.DHT22(Pin(16))
pir_sensor = Pin(23, Pin.IN)

# MQTT Configuration
mqtt_broker = "192.168.43.212"
mqtt_client_id = "esp32-sensor"
sensor_topic = "sensor_data"
client = None

# Wi-Fi Connection
async def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect('666wifipassword', '1133335678')
    while not wlan.isconnected():
        await asyncio.sleep(1)
    print('Connected to Wi-Fi:', wlan.ifconfig()[0])

# MQTT Connection
async def connect_mqtt():
    global client
    try:
        client = MQTTClient(mqtt_client_id, mqtt_broker, port=1883)
        client.connect(clean_session=False)
        client.set_last_will(sensor_topic, "Disconnected")
        print("Connected to MQTT broker")
    except OSError as e:
        print(f"Failed to connect to MQTT broker: {e}")

# Reading Sensor Data
async def reading_sensor():
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
async def check_pir():
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
        await asyncio.sleep(1)

# Main Function
async def main():
    print("Waiting For Power On Warm Up")
    await asyncio.sleep(5)
    print("Ready!")

    await connect_wifi()
    await connect_mqtt()

    # Run sensor reading and PIR checking concurrently
    asyncio.create_task(reading_sensor())
    await check_pir()

try:
    asyncio.run(main())
except KeyboardInterrupt:
    print("Disconnected from Broker")
    if client:
        client.disconnect()
