from machine import Pin
from umqtt.simple import MQTTClient
import time
import esp32
import gc
import json
import network  # สำหรับการเชื่อมต่อ Wi-Fi

gc.collect()

# ตั้งค่า GPIO Pin สำหรับ PIR Sensors
PIR_SENSOR_1_PIN = 23  # PIR sensor ตัวที่ 1
PIR_SENSOR_2_PIN = 16  # PIR sensor ตัวที่ 2
pir_sensor_1 = Pin(PIR_SENSOR_1_PIN, Pin.IN)
pir_sensor_2 = Pin(PIR_SENSOR_2_PIN, Pin.IN)

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

# ตรวจจับการเดินเข้าและออกจากห้อง
last_triggered = None

def check_pir():
    global last_triggered
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

print("Waiting For Power On Warm Up")
time.sleep(3)  # Power On Warm Up Delay
print("Ready!")

# เชื่อมต่อ Wi-Fi
connect_wifi()

# เชื่อมต่อ MQTT
connect_mqtt()

while True:
    try:
        check_pir()
        time.sleep(0.5)  # ลดเวลาหน่วงเพื่อให้การตรวจจับเร็วขึ้น
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
        time.sleep(5)
        connect_mqtt()
