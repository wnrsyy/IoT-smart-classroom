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
    wlan.connect('666wifipassword', '1133335678')  # ใส่ชื่อและรหัสผ่าน Wi-Fi ของคุณ
    while not wlan.isconnected():
        time.sleep(1)
    print('Connected to Wi-Fi, IP address:', wlan.ifconfig()[0])

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

def reading_sensor():
    try:
        sensor.measure()
        temperature_dht = sensor.temperature()
        humidity_dht = sensor.humidity()
        temperature_esp32 = (esp32.raw_temperature() - 32.0) / 1.8

        print("Temperature (DHT): {}C, Humidity (DHT): {}%, Temperature (ESP32): {:.2f}C".format(temperature_dht, humidity_dht, temperature_esp32))
        payload = {
            'temperature': temperature_dht,
            'humidity': humidity_dht,
            'esp32Temperature': temperature_esp32
        }
        if client:
            client.publish(sensor_topic, json.dumps(payload))
    except OSError:
        print("Please check sensor")
had_object = False
counter = 0
def check_pir():
    global warm_up, had_object, counter
    sensor_output = pir_sensor.value()
    if sensor_output == 0 | had_object:
        had_object = False
        if warm_up == 1:
            warm_up = 0
        #print("Nobody here (--!)\n")
    else:
        counter += 1
        print("I'm here! counter :", counter,"\n")
        had_object = True
        warm_up = 1

print("Waiting For Power On Warm Up")
time.sleep(3)  # Power On Warm Up Delay
print("Ready!")

warm_up = 0

# เชื่อมต่อ Wi-Fi ก่อน
connect_wifi()

# เชื่อมต่อ MQTT
connect_mqtt()

while True:
    try:
        #reading_sensor()
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
        time.sleep(5)  # wait before retrying
        connect_mqtt()
