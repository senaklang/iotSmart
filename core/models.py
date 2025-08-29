from app import db
from datetime import datetime
import pytz

class SensorData(db.Model):
    __tablename__ = 'sensor_data'
    
    timestamp = db.Column(db.DateTime, default=datetime.now, index=True)
    timestamp = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(pytz.timezone('Asia/Bangkok')))
    
    id = db.Column(db.Integer, primary_key=True)
    temperature = db.Column(db.Float)
    humidity = db.Column(db.Float)
    tds = db.Column(db.Float)
    ph = db.Column(db.Float)
    ec = db.Column(db.Float)
    timestamp = db.Column(db.DateTime, default=datetime.now)

    def __repr__(self):
        return f'<SensorData {self.id} {self.timestamp}>'
    
# 🆕 ฐานข้อมูล lamp.db
class LampData(db.Model):
    __bind_key__ = 'lamp'  # ชี้ไปยัง lamp.db
    __tablename__ = 'lamp_data'

    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String(10))
    timestamp = db.Column(db.DateTime)