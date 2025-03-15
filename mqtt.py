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
sensor_out = dht.DHT11(Pin(16))
sensor_in = dht.DHT22(Pin(14))

# setting GPIO Pin for PIR sensor
PIR_SENSOR_OUTPUT_PIN = 23  # กำหนดขา PIR sensor
pir_sensor = Pin(PIR_SENSOR_OUTPUT_PIN, Pin.IN)

# LED Pin
LED_PIN = 26
led = Pin(LED_PIN, Pin.OUT)

# MQTT Configuration
mqtt_broker = "192.168.43.212"
mqtt_client_id = "esp32-sensor"
sensor_topic = "sensor_data"
led_status_topic = "device/led/status"  # หัวข้อสำหรับสถานะ LED

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

import json

def reading_sensor():
    try:
        sensor_out.measure()
        temp_out_c = sensor_out.temperature()
        temp_out_f = (temp_out_c * 9/5) + 32
        humi_out = sensor_out.humidity()
        
        sensor_in.measure()
        temp_in_c = sensor_in.temperature()
        temp_in_f = (temp_in_c * 9/5) + 32
        humi_in = sensor_in.humidity()

        # แสดงข้อมูลเซ็นเซอร์
        print("Temperature outside room")
        print(f"Celsius temp: {temp_out_c:.2f}°C, Fahrenheit temp: {temp_out_f:.2f}°F, Humidity: {humi_out:.2f}%\n")

        print("Temperature inside room")
        print(f"Celsius temp: {temp_in_c:.2f}°C, Fahrenheit temp: {temp_in_f:.2f}°F, Humidity: {humi_in:.2f}%\n")

        check_pir()

        data = {
            "temp_out_c": temp_out_c,
            "temp_out_f": temp_out_f,
            "humi_out" : humi_out,
            "temp_in_c": temp_in_c,
            "temp_in_f": temp_in_f,
            "humi_in" : humi_in,
        }

        # กำหนดสถานะ LED ตามเงื่อนไข
        led_status = "ON" if temp_in_c < temp_out_c else "OFF"

        # ส่งข้อมูลทั้งหมดผ่าน MQTT
        publish_mqtt(data, led_status)
        
        # ควบคุม LED
        if led_status == "ON":
            led.on()
            print("LED ON (temp_in < temp_out)\n")
        else:
            led.off()
            print("LED OFF (temp_in >= temp_out)\n")

    except Exception as e:
        print("Error reading sensor:", e)

def publish_mqtt(data, led_status):
    if client:
        # รวมข้อมูลสถานะ LED กับข้อมูลเซ็นเซอร์
        data["led_status"] = led_status
        payload = json.dumps(data)

        print(f"Publishing to MQTT: {sensor_topic}, {payload}")
        client.publish(sensor_topic, payload)

        print(f"Publishing to MQTT: {led_status_topic}, {led_status}\n")
        client.publish(led_status_topic, led_status)
    else:
        print("MQTT client not connected!")

def check_pir():
    global warm_up
    sensor_output = pir_sensor.value()
    if sensor_output == 0:
        if warm_up == 1:
            warm_up = 0
        print("Nobody here (--!)")
        print("---------------------------------------------")
    else:
        print("I'm here \(^O^)/")
        print("---------------------------------------------")
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