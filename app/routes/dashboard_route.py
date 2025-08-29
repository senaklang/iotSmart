from flask import Blueprint, render_template, jsonify
from core.hardware_interface import HardwareInterface, SensorData
from datetime import datetime, timedelta

dashboard_bp = Blueprint('dashboard', __name__)
hardware = HardwareInterface()

@dashboard_bp.route('/')
@dashboard_bp.route('/dashboard')
def dashboard():
    # อ่านข้อมูลล่าสุดจากฐานข้อมูล
    latest_data = SensorData.query.order_by(SensorData.timestamp.desc()).first()
    return render_template('dashboard.html', data=latest_data)

@dashboard_bp.route('/api/sensor-data')
def get_sensor_data():
    # อ่านข้อมูลจากฮาร์ดแวร์โดยตรง
    hardware_data = hardware.read_sensor_data()
    
    if hardware_data:
        # บันทึกลงฐานข้อมูล
        new_record = SensorData(
            temperature=hardware_data['temperature'], # type: ignore
            humidity=hardware_data['humidity'],# type: ignore
            tds=hardware_data['tds'],# type: ignore
            ph=hardware_data['ph']# type: ignore
        )
        db.session.add(new_record)# type: ignore
        db.session.commit()# type: ignore
        
        return jsonify({
            'status': 'success',
            'data': hardware_data,
            'timestamp': datetime.now().isoformat()
        })
    else:
        # หากอ่านจากฮาร์ดแวร์ไม่ได้ ให้ใช้ข้อมูลล่าสุดจากฐานข้อมูล
        last_record = SensorData.query.order_by(SensorData.timestamp.desc()).first()
        if last_record:
            return jsonify({
                'status': 'warning',
                'message': 'Using last recorded data',
                'data': {
                    'temperature': last_record.temperature,
                    'humidity': last_record.humidity,
                    'tds': last_record.tds,
                    'ph': last_record.ph
                },
                'timestamp': last_record.timestamp.isoformat()
            })
        return jsonify({
            'status': 'error',
            'message': 'No sensor data available'
        }), 500