from machine import Pin
from umqtt.simple import MQTTClient
import time
import esp32
import dht
import gc
import json
import network

gc.collect()


# GPIO Pins for DHT22 sensors
inside_sensor = dht.DHT22(Pin(16))
outside_sensor = dht.DHT22(Pin(17))

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

# Variables for tracking temperature changes
last_inside_temperature = None
last_inside_timestamp = time.time()

# Function to read temperatures and detect A/C status
def reading_sensor():
    global last_inside_temperature, last_inside_timestamp
    
    try:
        inside_sensor.measure()
        outside_sensor.measure()
        
        inside_temp = inside_sensor.temperature()  # Inside room (Celsius)
        outside_temp = outside_sensor.temperature()  # Outside room (Celsius)
        humidity = inside_sensor.humidity()  # Use inside sensor for humidity
        temperature_esp32 = esp32.raw_temperature()  # ESP32 internal temp (Celsius)
        
        # Get current time
        current_timestamp = time.time()

        # A/C detection based on inside temperature (every 5 minutes)
        ac_status = "unknown"
        if last_inside_temperature is not None and (current_timestamp - last_inside_timestamp) >= 300:  # 5 minutes
            temp_change = inside_temp - last_inside_temperature  # Change in inside temp
            
            if temp_change <= -1.0:  # Decreased by 1°C (A/C ON)
                ac_status = "on"
            elif temp_change >= 1.0:  # Increased by 1°C (A/C OFF)
                ac_status = "off"
            
            # Update last recorded inside temperature and timestamp
            last_inside_temperature = inside_temp
            last_inside_timestamp = current_timestamp
        
        # First-time temperature storage
        if last_inside_temperature is None:
            last_inside_temperature = inside_temp
        
        # Compare Inside vs. Outside temperature
        temp_difference = inside_temp - outside_temp  # Inside temp - Outside temp

        # Prepare data for MQTT
        data = {
            "inside_temperature": inside_temp,
            "outside_temperature": outside_temp,
            "humidity": humidity,
            "esp32_temperature": temperature_esp32,
            "ac_status": ac_status,
            "temp_difference": temp_difference  # Inside vs Outside
        }
        payload = json.dumps(data)

        if client:
            print(f"Publishing to MQTT: {payload}")
            client.publish(sensor_topic, payload)
        else:
            print("MQTT client not connected!")

    except Exception as e:
        print("Error reading sensor:", e)

# PIR Sensor Detection
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
time.sleep(5)
print("Ready!")

warm_up = 0

# Connect Wi-Fi and MQTT
connect_wifi()
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
        time.sleep(2)
        connect_mqtt()
