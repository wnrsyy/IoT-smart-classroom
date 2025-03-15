import socket
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
from flask_mqtt import Mqtt
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json
import os
from sqlalchemy import text
from datetime import datetime

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
mqtt_sensor_topic = "sensor_data"
# mqtt_sensor_topic = "+"
# mqtt_relay_topic = "relay_controller"

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://miso:1234@10.161.112.160:5433/iot_smart_classroom_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

def test_db_connection():
    try:
        result = db.session.execute(text("SELECT * FROM smartclass_db LIMIT 1;"))
        print("✅ Database connected successfully: ", result.fetchone())
    except Exception as e:
        print("❌ Error connecting to database:", e)


def parse_sensor_data(data):
    try:
        print(f"📥 Received raw sensor data: {data}")  # Debug ตรงนี้

        sensor_data = json.loads(data)
        temp_out_c = sensor_data.get('temp_out_c', 0)
        temp_out_f = sensor_data.get('temp_out_f', 0)
        temp_in_c = sensor_data.get('temp_in_c', 0)
        temp_in_f = sensor_data.get('temp_in_f', 0)
        humi_out = sensor_data.get('humi_out', 0)
        humi_in = sensor_data.get('humi_in', 0)

        print(f"📊 Parsed sensor data: temp_out_c={temp_out_c}, temp_out_f={temp_out_f}, humi_out={humi_out}, temp_in_c={temp_in_c}, temp_in_f={temp_in_f}, humi_in={humi_in}")

        with app.app_context():
            send_db(temp_out_c, temp_out_f, humi_out, temp_in_c, temp_in_f, humi_in)

        return {
            'temp_out_c': temp_out_c,
            'temp_out_f': temp_out_f,
            'humi_out': humi_out,
            'temp_in_c': temp_in_c,
            'temp_in_f': temp_in_f,
            'humi_in': humi_in,
        }
    except json.JSONDecodeError as e:
        print(f"❌ Error decoding JSON: {e}")
        return None
    except Exception as e:
        print(f"❌ Error parsing sensor data: {e}")
        return None


def send_db(temp_out_c, temp_out_f, humi_out, temp_in_c, temp_in_f, humi_in):
    try:
        current_time = datetime.now()
        date_time = current_time.strftime("%Y-%m-%d %H:%M:%S")

        query = text("""
            INSERT INTO smartclass_db (temp_out_c, temp_out_f, humi_out, temp_in_c, temp_in_f, humi_in, timestamp)
            VALUES (:temp_out_c, :temp_out_f, :humi_out, :temp_in_c, :temp_in_f, :humi_in, :timestamp)
        """)

        db.session.execute(query, {
            'temp_out_c': temp_out_c,
            'temp_out_f': temp_out_f,
            'humi_out': humi_out,
            'temp_in_c': temp_in_c,
            'temp_in_f': temp_in_f,
            'humi_in': humi_in,
            'timestamp': date_time
        })

        db.session.commit()
        print(f"✅ Data inserted: {temp_out_c}, {temp_out_f}, {humi_out}, {temp_in_c}, {temp_in_f}, {humi_in}, {date_time}")

    except Exception as e:
        db.session.rollback()
        print(f"❌ Error inserting data: {e}")

@app.route('/api/sensor_data', methods=['GET'])
def get_sensor_data():
    try:
        query = text("SELECT * FROM smartclass_db ORDER BY timestamp DESC LIMIT 10;")  
        result = db.session.execute(query)
        data = [dict(row) for row in result.mappings()]
        return jsonify({'status': 'success', 'data': data}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500



# MQTT
@mqtt.on_connect()
def handle_connect(client, userdata, flags, rc):
    client.subscribe("sensor_data")  # ข้อมูลอุณหภูมิ
    client.subscribe("device/led/status")  # รับค่าสถานะ LED
    client.subscribe("room/people_count") 
    print("Connected to MQTT Broker")

@mqtt.on_message()
def handle_mqtt_message(client, userdata, message):
    data = message.payload.decode()
    print(f"Received MQTT message on {message.topic}: {data}")

    if message.topic == "sensor_data":
        try:
            parsed_data = parse_sensor_data(data)
            if parsed_data:
                socketio.emit('sensorData', parsed_data, namespace='/')
        except Exception as e:
            print(f"Error parsing sensor data: {e}")

    elif message.topic == "device/led/status":
        print(f"LED Status: {data}")
        socketio.emit('ledStatus', {'led_status': data}, namespace='/')

    elif message.topic == "room/people_count":
        print(f"People count: {data}")
        socketio.emit('peopleCount', {'people_count': data}, namespace='/')

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
    # socketio.run(app, host='0.0.0.0', port=5000, debug=True)
    socketio.run(app, host='0.0.0.0', port=5000)