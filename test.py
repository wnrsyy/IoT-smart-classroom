import psycopg2

try:
    conn = psycopg2.connect(
        dbname="iot_smart_classroom_db",
        user="miso",
        password="1234",
        host="10.161.112.160",
        port="5432"  # ตรวจสอบว่าคุณใช้ 5432 หรือ 1884 จริงๆ
    )
    print("✅ Connected successfully!")
    conn.close()
except Exception as e:
    print("❌ Connection failed:", e)
