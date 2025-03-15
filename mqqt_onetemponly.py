from machine import Pin
from umqtt.simple import MQTTClient
import time
import dht
import gc
import json
import network

gc.collect()

# GPIO Pins for DHT22 sensors
inside_sensor = dht.DHT22(Pin(16))  # Inside room
outside_sensor = dht.DHT22(Pin(17))  # Outside room

# PIR sensor for motion detection
PIR_SENSOR_OUTPUT_PIN = 23
pir_sensor = Pin(PIR_SENSOR_OUTPUT_PIN, Pin.IN)

# MQTT Configuration
mqtt_broker = "192.168.43.212"
mqtt_client_id = "esp32-sensor"
sensor_topic = "sensor_data"

client = None

# Wi-Fi Connection
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print('Connecting to Wi-Fi...')
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
        client = MQTTClient(mqtt_client_id, mqtt_broker, port=1883, user=None, password=None, keepalive=300, ssl=False)
        client.connect(clean_session=False)
        client.set_last_will(sensor_topic, "Disconnected")
        print("Connected to MQTT broker")
    except OSError as e:
        print("Failed to connect to MQTT broker: ", e)
        time.sleep(5)
        connect_mqtt()

def disconnect_mqtt():
    global client
    if client:
        try:
            client.disconnect()
            print("Disconnected from MQTT broker")
        except OSError as e:
            print("Error disconnecting MQTT: ", e)

# Function to read temperature when motion is detected
def read_temperature():
    try:
        inside_sensor.measure()
        outside_sensor.measure()

        inside_temp = inside_sensor.temperature()  # Inside room temperature (°C)
        outside_temp = outside_sensor.temperature()  # Outside room temperature (°C)
        humidity = inside_sensor.humidity()  # Humidity from inside sensor

        # Compare Inside vs. Outside temperature
        temp_difference = inside_temp - outside_temp

        # Prepare data for MQTT
        data = {
            "inside_temperature": inside_temp,
            "outside_temperature": outside_temp,
            "humidity": humidity,
            "temp_difference": temp_difference
        }
        payload = json.dumps(data)

        if client:
            print(f"Publishing to MQTT: {payload}")
            client.publish(sensor_topic, payload)
        else:
            print("MQTT client not connected!")

    except Exception as e:
        print("Error reading sensor:", e)

# Function to check PIR sensor and trigger temperature reading
def check_motion():
    if pir_sensor.value() == 1:  # Motion detected
        print("Motion detected! Reading temperature...")
        read_temperature()
    else:
        print("No motion detected.")

# Connect Wi-Fi and MQTT
connect_wifi()
connect_mqtt()

print("System Ready! Waiting for motion...")

while True:
    try:
        check_motion()
        time.sleep(1)
    except OSError as e:
        print("Error: ", e)
        disconnect_mqtt()
        time.sleep(5)
    except KeyboardInterrupt:
        disconnect_mqtt()
        print("Disconnected from MQTT")
        break
    except Exception as e:
        print(f"Unexpected error: {e}")
        time.sleep(2)
        connect_mqtt()
