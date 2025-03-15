from machine import Pin
from umqtt.simple import MQTTClient
import time
import esp32
import dht
import gc
import json
import network  # สำหรับการเชื่อมต่อ Wi-Fi

gc.collect()

# setting GPIO Pin for DHT22 sensor
sensor = dht.DHT22(Pin(16))

# setting GPIO Pin for PIR sensor
PIR_SENSOR_OUTPUT_PIN = 23  # กำหนดขา PIR sensor
pir_sensor = Pin(PIR_SENSOR_OUTPUT_PIN, Pin.IN)

# MQTT Configuration
mqtt_broker = "192.168.43.212"
mqtt_client_id = "esp32-sensor"
sensor_topic = "sensor_data"

client = None

# ตั้งค่า Wi-Fi
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print('Connecting to Wi-Fi...')
        wlan.connect('666wifipassword', '1133335678')  
        timeout = 10  # Timeout for connection attempt
        while not wlan.isconnected() and timeout > 0:
            time.sleep(1)
            timeout -= 1
    if wlan.isconnected():
        print('Connected to Wi-Fi:', wlan.ifconfig()[0])
    else:
        print("Failed to connect to Wi-Fi. Restarting...")
        machine.reset()


def connect_mqtt():
    global client
    try:
        print(f"Attempting to connect to MQTT broker at {mqtt_broker}...")
        client = MQTTClient(mqtt_client_id, mqtt_broker, port=1883, user="username", password="password", keepalive=300, ssl=False)
        client.connect(clean_session=False)
        client.set_last_will(sensor_topic, "Disconnected")
        print("Connected to MQTT broker")
    except OSError as e:
        print("Failed to connect to MQTT broker: ", e)
        time.sleep(5)
        connect_mqtt()  # Retry
    except Exception as e:
        print(f"Unexpected error: {e}")
        time.sleep(5)
        connect_mqtt()  # Retry


def disconnect_mqtt():
    global client
    if client:
        try:
            client.disconnect()
            print("Disconnected from MQTT broker")
        except OSError as e:
            print("Error disconnecting MQTT: ", e)

def reading_sensor():
    try:
        sensor.measure()
        temperature = sensor.temperature()
        humidity = sensor.humidity()
        esp32Temperature = (esp32.raw_temperature() - 32.0) / 1.8

        print(f"Temperature (DHT): {temperature}C, Humidity (DHT): {humidity}%, Temperature (ESP32): {esp32Temperature}C")

        data = {
            "temperature": temperature,
            "humidity": humidity,
            "esp32_temperature": esp32Temperature
        }

        payload = json.dumps(data)
        
        if client:
            
            payload = json.dumps(data)
            print(f"Publishing to MQTT: {payload}")
            client.publish(sensor_topic, payload)

        else:
            print("MQTT client not connected!")

    except Exception as e:
        print("Error reading sensor:", e)


def check_pir():
    global warm_up
    sensor_output = pir_sensor.value()
    if sensor_output == 0:
        if warm_up == 1:
            warm_up = 0
        print("Nobody here (--!)\n")
    else:
        print("I'm here!\n")
        warm_up = 1

print("Waiting For Power On Warm Up")
time.sleep(5)  # Power On Warm Up Delay
print("Ready!")

warm_up = 0

# เชื่อมต่อ Wi-Fi ก่อน
connect_wifi()

# เชื่อมต่อ MQTT
connect_mqtt()

while True:
    try:
        reading_sensor()
        check_pir()
        time.sleep(1)
    except OSError as e:
        print("Error reading sensor: ", e)
        disconnect_mqtt()
        time.sleep(5)
    except KeyboardInterrupt:
        disconnect_mqtt()
        print("Disconnected from Broker")
        break
    except Exception as e:
        print(f"Unexpected error: {e}")
        time.sleep(2)  # wait before retrying
        connect_mqtt()
