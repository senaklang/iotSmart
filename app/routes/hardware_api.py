# app/routes/hardware_api.py
from app import db
from core.models import LampData, SensorData
from core.hardware_interface import HardwareInterface
from flask import Blueprint, request, jsonify, current_app
from datetime import datetime, timedelta
import random

hardware_bp = Blueprint('hardware', __name__, url_prefix='/hardware')

@hardware_bp.route('/com-status')
def com_status():
    hw = current_app.config.get('hardware_interface')
    
    if hw is None:
        return jsonify({'error': 'Hardware interface not initialized'}), 500

    # ใช้เมธอด get_connection_info() ที่สร้างใหม่
    connection_info = hw.get_connection_info()
    #print(connection_info)
    return jsonify({'connected': connection_info})

@hardware_bp.route('/lamp/lampcontrol', methods=['GET', 'POST'])
def lamp_control():
    if request.method == 'POST':
        data = request.get_json(silent=True) or {}
        device_id = data.get('device_id')
        action = data.get('action')
        channel = data.get('channel')
    else:  # GET
        device_id = request.args.get('device_id')
        action = request.args.get('action')
        channel = request.args.get('channel')

    # ตรวจสอบ parameter
    if None in (device_id, action, channel):
        return jsonify({'status': 'error', 'message': 'Missing params'}), 400

    hw = current_app.config.get('hardware_interface')
    if not hw:
        return jsonify({'status': 'error', 'message': 'Hardware interface not initialized'}), 500

    ok = hw.control_lamp(str(device_id), str(action), str(channel))
    if ok:
        return jsonify({'status': 'success', 'message': 'Command queued/sent'}), 200
    else:
        return jsonify({'status': 'warning', 'message': 'Queued but immediate send failed'}), 200


# ✅ GET: อ่านสถานะหลอดไฟทั้งหมด
@hardware_bp.route('/lamp/status', methods=['GET'])
def get_lamp_status():
    try:
        lamps = LampData.query.all()
        if not lamps:
            return jsonify({'status': 'error', 'message': 'No lamp data available'}), 404

        lamps_data = [
            {
                'id': lamp.id,
                'status': lamp.status,
                'timestamp': lamp.timestamp.isoformat() if lamp.timestamp else None
            }
            for lamp in lamps
        ]
        return jsonify({'status': 'success', 'data': lamps_data})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ✅ PUT: อัพเดทสถานะของหลอดไฟตาม id
@hardware_bp.route('/lamp/status/<int:lamp_id>', methods=['PUT'])
def update_lamp_status(lamp_id):
    try:
        data = request.get_json()
        status = data.get('status')

        lamp = LampData.query.get(lamp_id)
        if not lamp:
            return jsonify({'status': 'error', 'message': 'Lamp not found'}), 404

        # อัพเดต DB
        lamp.status = status
        lamp.timestamp = datetime.utcnow()
        db.session.commit()

        # ส่งคำสั่งไป Arduino ด้วย hardware_interface
        hw = current_app.config.get('hardware_interface')
        if hw:
            ok = hw.control_lamp("position", status, lamp_id)
            print(ok)
            if not ok:
                return jsonify({
                    'status': 'warning',
                    'message': 'DB updated but failed to send to hardware'
                }), 202
        else:
            return jsonify({
                'status': 'warning',
                'message': 'DB updated but hardware interface not available'
            }), 202

        return jsonify({'status': 'success', 'message': f'Lamp {lamp_id} set to {status}'})

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@hardware_bp.route('/sensor/sensor-data')
def sensor_data():
    try:
        # อ่านข้อมูลจากฮาร์ดแวร์
        hardware_interface = HardwareInterface()
        hardware_data = hardware_interface.read_sensor_data()
        
        if hardware_data:
            # บันทึกลงฐานข้อมูล
            new_record = SensorData(
                temperature=hardware_data['temperature'], # type: ignore
                humidity=hardware_data['humidity'], # type: ignore
                tds=hardware_data['tds'], # type: ignore
                ph=hardware_data['ph'], # type: ignore
                ec=hardware_data.get('ec') or round(random.uniform(1.0, 3.0), 2)  # type: ignore
            )
            db.session.add(new_record)
            db.session.commit()
            
            return jsonify({
                'status': 'success',
                'source': 'hardware',
                'data': hardware_data,
                'timestamp': datetime.now().isoformat()
            })
        
        # หากอ่านจากฮาร์ดแวร์ไม่ได้
        last_record = SensorData.query.order_by(SensorData.timestamp.desc()).first()
        if last_record:
            return jsonify({
                'status': 'success',
                'source': 'database',
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
        }), 404
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@hardware_bp.route('/sensor/current')
def get_current_sensor_data():
    try:
        # 1. รับ hardware interface จาก app config
        hw = current_app.config.get('hardware_interface')
        if not hw:
            raise RuntimeError("Hardware interface not initialized")
        
        # 2. พยายามอ่านจากฮาร์ดแวร์
        hardware_data = None
        if hw.is_connected():  # ตรวจสอบการเชื่อมต่อก่อนอ่านค่า
            hardware_data = hw.read_sensor_data()
        
        if hardware_data:
            # บันทึกข้อมูลใหม่
            new_record = SensorData(
                temperature=hardware_data.get('temperature'), # type: ignore
                humidity=hardware_data.get('humidity'),# type: ignore
                tds=hardware_data.get('tds'),# type: ignore
                ph=hardware_data.get('ph'),# type: ignore
                ec=hardware_data.get('ec', round(random.uniform(1.0, 3.0), 2))# type: ignore
            )
            db.session.add(new_record)
            db.session.commit()
            
            return jsonify({
                'status': 'success',
                'source': 'hardware',
                'data': hardware_data,
                'timestamp': datetime.now().isoformat()
            })
        
        # 3. หากอ่านจากฮาร์ดแวร์ไม่ได้ ให้ใช้ข้อมูลล่าสุดจากฐานข้อมูล
        last_record = SensorData.query.order_by(SensorData.timestamp.desc()).first()
        if last_record:
            return jsonify({
                'status': 'success',
                'source': 'database',
                'data': {
                    'temperature': last_record.temperature,
                    'humidity': last_record.humidity,
                    'tds': last_record.tds,
                    'ph': last_record.ph,
                    'ec': last_record.ec
                },
                'timestamp': last_record.timestamp.isoformat()
            })
            
        return jsonify({
            'status': 'error', 
            'message': 'No sensor data available from hardware or database'
        }), 404
        
    except Exception as e:
        current_app.logger.error(f"Sensor data error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to get sensor data',
            'details': str(e)
        }), 500
