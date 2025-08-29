from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import serial
import time


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sensor_data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# โมเดลสำหรับเก็บข้อมูลเซ็นเซอร์
class Hardware_db(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    temperature = db.Column(db.Float)
    humidity = db.Column(db.Float)
    tds = db.Column(db.Float)
    ph = db.Column(db.Float)
    timestamp = db.Column(db.DateTime, default=datetime.now)

    def __repr__(self):
        return f'<SensorData {self.id} {self.timestamp}>'

    # สร้างฐานข้อมูลหากยังไม่มี
    with app.app_context():
        db.create_all()

    def get_serial_connection(self):
        try:
            return serial.Serial('COM5', 115200, timeout=1)
        except serial.SerialException as e:
            print("เชื่อมต่อ COM4 ไม่สำเร็จ:", e)
            return None
'''
    def read_sensor_data(self):
        ser = self.get_serial_connection()
        if ser is None:
            return None

        try:
            ser.write(b'GET_SENSORS\n')
            time.sleep(1.0)

            start_time = time.time()
            while time.time() - start_time < 3.0:
                if ser.in_waiting:
                    line = ser.readline().decode('utf-8', errors='ignore').strip()
                    print("ได้ข้อมูล:", line)

                    if not line.startswith("Temp:"):
                        continue

                    parts = line.replace('°C', '').replace('%', '').replace('ppm', '').split(',')
                    data = {}
                    for part in parts:
                        if ':' in part:
                            key, value = part.strip().split(':')
                            data[key.strip()] = value.strip()

                    if all(k in data for k in ['Temp', 'Humidity', 'TDS', 'PH']):
                        new_data = Hardware_db()
                        new_data.temperature = float(data['Temp'])
                        new_data.humidity = float(data['Humidity'])
                        new_data.tds = float(data['TDS'])
                        new_data.ph = float(data['PH'])
                        db.session.add(new_data)
                        db.session.commit()
                        return data
            return None
        except Exception as e:
            print("ERROR:", str(e))
            return None
        finally:
            if ser:
                ser.close()
'''