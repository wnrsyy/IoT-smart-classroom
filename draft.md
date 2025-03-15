import socket
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
from flask_mqtt import Mqtt
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json
import logging
from datetime import datetime

# ตั้งค่า logging
logging.basicConfig(filename='sensor_log.txt', level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__, template_folder="www/")
app.config['SECRET_KEY'] = 'secret_key'

app.config['MQTT_BROKER_URL'] = '192.168.43.212'
app.config['MQTT_BROKER_PORT'] = 1883
app.config['MQTT_USERNAME'] = ''
app.config['MQTT_PASSWORD'] = ''
app.config['MQTT_KEEPALIVE'] = 300
app.config['MQTT_TLS_ENABLED'] = False
topic = "+"

socketio = SocketIO(app)
mqtt = Mqtt(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://miso:1234@10.161.112.160:5433/iot_smart_classroom_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

def test_db_connection():
    try:
        result = db.session.execute("SELECT * FROM sensor_data;")
        print("✅ Database connected successfully: ", result.fetchone())
    except Exception as e:
        print("❌ Error connecting to database:", e)

def parse_sensor_data(data):
    try:
        sensor_data = json.loads(data)
        temperature_celsius = sensor_data.get('temperature_celsius', 0)
        humidity = sensor_data.get('humidity', 0)
        temperature_fahrenheit = sensor_data.get('temperature_fahrenheit', 0)

        with app.app_context():
            send_db(temperature_celsius, humidity, temperature_fahrenheit)

        return {
            'celsius': temperature_celsius,
            'humidity': humidity,
            'fahrenheit': temperature_fahrenheit
        }
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        return None
    except Exception as e:
        print(f"Error parsing sensor data: {e}")
        return None

def send_db(data):
    try:
        logging.info("send_db function called")
        logging.info(f"Received values -> Celsius: {data['celsius']}, Fahrenheit: {data['fahrenheit']}, Humidity: {data['humidity']}")
        logging.info("Connecting to database...")

        # อุณหภูมิภายในห้อง (ในเซลเซียส และฟาเรนไฮต์)
        temp_in_c = data['celsius']
        temp_in_f = data['fahrenheit']

        # อุณหภูมิภายนอกห้อง (ในเซลเซียส และฟาเรนไฮต์) คุณสามารถแทนค่าของ `temp_out_c` และ `temp_out_f` ได้ตามที่ต้องการ
        temp_out_c = 25  # ตัวอย่างค่าภายนอกห้อง (คุณอาจจะต้องนำค่าจริงจากเซนเซอร์ภายนอก)
        temp_out_f = (temp_out_c * 9/5) + 32  # เปลี่ยนจากเซลเซียสเป็นฟาเรนไฮต์

        # ความชื้น (humi_in: ภายในห้อง, humi_out: ภายนอกห้อง)
        humi_in = data['humidity']
        humi_out = 60  # ตัวอย่างค่าภายนอกห้อง (เช่นเดียวกันกับภายนอกห้อง คุณสามารถใช้ค่าจริงจากเซนเซอร์ภายนอก)

        # กำหนดเวลาปัจจุบัน
        current_time = datetime.now()
        date_time = current_time.strftime("%Y-%m-%d %H:%M:%S")

        logging.info("Executing SQL command...")

        # แทรกข้อมูลลงในตาราง smartclass
        db.session.execute(
            """
            INSERT INTO smartclass (temp_in_c, temp_in_f, temp_out_c, temp_out_f, humi_in, humi_out, timestamp)
            VALUES (:temp_in_c, :temp_in_f, :temp_out_c, :temp_out_f, :humi_in, :humi_out, :timestamp)
            """,
            {
                'temp_in_c': temp_in_c,
                'temp_in_f': temp_in_f,
                'temp_out_c': temp_out_c,
                'temp_out_f': temp_out_f,
                'humi_in': humi_in,
                'humi_out': humi_out,
                'timestamp': date_time
            }
        )
        db.session.commit()
        logging.info("Insert data successful")
    except Exception as e:
        logging.error(f"Error while inserting data: {e}")
        db.session.rollback()
        return "error"

# MQTT
@mqtt.on_connect()
def handle_connect(client, userdata, flags, rc):
    mqtt.subscribe("+")
    print("Connected to MQTT Broker")

@mqtt.on_message()
def handle_message(client, userdata, message):
    data = message.payload.decode()
    print(f"Received MQTT message: {data}")
    if message.topic == "sensor_data":
        try:
            parsed_data = parse_sensor_data(data)
            if parsed_data:
                print(f"Parsed data: {parsed_data}")
                print(f"Data to emit: {parsed_data}")  # ตรวจสอบข้อมูลก่อน emit
                socketio.emit('sensorData', parse_sensor_data(data), namespace='/')
            else:
                print("Parsed data is None")
        except Exception as e:
            print(f"Error parsing data: {e}")
            return

@socketio.on('connect')
def on_connect():
    print('Client connected')
    socketio.emit('message', 'Connected to server')

@socketio.on('disconnect')
def on_disconnect():
    print('Client disconnected')
    socketio.emit('message', 'state: disconnected')

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        test_db_connection()
        print("Database connected successfully")
    print("Server is running on http://127.0.0.1:5000/")
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)

นี่คือไฟล์ app.py ที่ใช้รับข้อมูลจากบอร์ดแล้วแสดงผลหน้าเว็บ
เปลี่ยนตัวแปรที่ใช้ร่วมกันให้เหมือนกัน