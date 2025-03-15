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
PIR_IN_PIN = 23   # ตรวจจับคนเข้า
PIR_OUT_PIN = 27  # ตรวจจับคนออก
pir_in = Pin(PIR_IN_PIN, Pin.IN)
pir_out = Pin(PIR_OUT_PIN, Pin.IN)

# LED Pin
LED_PIN = 26
led = Pin(LED_PIN, Pin.OUT)

# MQTT Configuration
mqtt_broker = "10.161.112.160"
mqtt_client_id = "esp32-sensor"
sensor_topic = "sensor_data"
led_status_topic = "device/led/status"
people_count_topic = "room/people_count"  # หัวข้อ MQTT สำหรับจำนวนคนในห้อง

client = None
people_count = 0  # ตัวแปรนับจำนวนคน

# ตั้งค่า Wi-Fi
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
    global people_count
    try:
        sensor_out.measure()
        temp_out_c = sensor_out.temperature()
        temp_out_f = (temp_out_c * 9/5) + 32
        humi_out = sensor_out.humidity()
        
        sensor_in.measure()
        temp_in_c = sensor_in.temperature()
        temp_in_f = (temp_in_c * 9/5) + 32
        humi_in = sensor_in.humidity()

        print("Temperature outside room")
        print(f"Celsius temp: {temp_out_c:.2f}°C, Fahrenheit temp: {temp_out_f:.2f}°F, Humidity: {humi_out:.2f}%\n")

        print("Temperature inside room")
        print(f"Celsius temp: {temp_in_c:.2f}°C, Fahrenheit temp: {temp_in_f:.2f}°F, Humidity: {humi_in:.2f}%\n")

        check_pir()  # ตรวจจับการเข้าออกของคน

        data = {
            "temp_out_c": temp_out_c,
            "temp_out_f": temp_out_f,
            "humi_out": humi_out,
            "temp_in_c": temp_in_c,
            "temp_in_f": temp_in_f,
            "humi_in": humi_in,
            "people_count": people_count
        }

        led_status = "ON" if temp_in_c < temp_out_c else "OFF"

        if led_status == "ON":
            led.on()
            print("LED ON (temp_in < temp_out)\n")
        else:
            led.off()
            print("LED OFF (temp_in >= temp_out)\n")
            
        publish_mqtt(data, led_status)

    except Exception as e:
        print("Error reading sensor:", e)

def check_pir():
    global people_count

    pir_in_state = pir_in.value()
    pir_out_state = pir_out.value()

    if pir_in_state == 1 and pir_out_state == 0:
        people_count += 1
        print(f"Person entered! Current count: {people_count}\n")
        time.sleep(1.5)  # หน่วงเวลาเพื่อป้องกันการนับซ้ำ

    elif pir_out_state == 1 and pir_in_state == 0:
        if people_count > 0:
            people_count -= 1
        print(f"Person left! Current count: {people_count}\n")
        time.sleep(1.5)  # หน่วงเวลาเพื่อป้องกันการนับซ้ำ
        
def publish_mqtt(data, led_status):
    if client:
        data["led_status"] = led_status
        payload = json.dumps(data)

        print(f"Publishing to MQTT: {sensor_topic}, {payload}")
        client.publish(sensor_topic, payload)

        print(f"Publishing to MQTT: {led_status_topic}, {led_status}")
        client.publish(led_status_topic, led_status)

        print(f"Publishing to MQTT: {people_count_topic}, {people_count}")
        client.publish(people_count_topic, str(people_count))
    else:
        print("MQTT client not connected!")

print("Waiting For Power On Warm Up")
time.sleep(5)
print("Ready!")

# เชื่อมต่อ Wi-Fi และ MQTT
connect_wifi()
connect_mqtt()

while True:
    try:
        reading_sensor()
        print("--------------------------------------------------");
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
        time.sleep(2)
        connect_mqtt()
