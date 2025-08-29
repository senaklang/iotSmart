from flask import Blueprint, render_template
from core.hardware_interface import HardwareInterface
from core.models import SensorData
from app import db
from datetime import datetime
hardware = HardwareInterface()

def read_sensor_data():
    """อ่านข้อมูลล่าสุดจากฮาร์ดแวร์"""
    hardware_data = hardware.read_sensor_data()

    if hardware_data:
        # บันทึกลงฐานข้อมูล
        new_record = SensorData(
            temperature=hardware_data['temperature'],  # type: ignore
            humidity=hardware_data['humidity'],        # type: ignore
            tds=hardware_data['tds'],                  # type: ignore
            ph=hardware_data['ph']                     # type: ignore
        )
        db.session.add(new_record)  # type: ignore
        db.session.commit()          # type: ignore
        
        return hardware_data
    
    return None

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@dashboard_bp.route('/dashboard')

def dashboard():
    
    data = read_sensor_data()
    print(data)
    return render_template('dashboard.html', data=data)
