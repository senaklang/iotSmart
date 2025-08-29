from flask import Blueprint, jsonify
from core.hardware_interface import HardwareInterface
from core.models import LampData
from app import db
from core.models import SensorData
from datetime import datetime
import pandas as pd
from flask import request 
from datetime import datetime, timedelta
import random


api_bp = Blueprint('api', __name__, url_prefix='/api')
        
from flask import Blueprint, jsonify, current_app

bp = Blueprint('hardware', __name__)

@bp.route('/com-status')
def com_status():
    hw = current_app.config.get('hardware_interface')
    if hw is None:
        return jsonify({'error': 'Hardware interface not initialized'}), 500

    return jsonify({'connected': hw.is_connected()})

@api_bp.route('/sensor/current')
def get_current_sensor_data():
    try:
        # ✅ ใช้ hardware interface ที่ share มาจาก app config
        hw = current_app.config.get('hardware_interface')
        if not hw:
            raise RuntimeError("Hardware interface not initialized")
        
        hardware_data = None
        # ✅ check ว่า hardware ต่ออยู่จริง
        if hw.is_connected():
            hardware_data = hw.read_sensor_data()
        
        if hardware_data:
            # ✅ บันทึกลง database ด้วย
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

        # ถ้า hardware อ่านไม่ได้ → fallback DB
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
            'message': 'No sensor data available'
        }), 404

    except Exception as e:
        current_app.logger.error(f"API sensor error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to get sensor data',
            'details': str(e)
        }), 500


@api_bp.route('/sensor/history')
def get_historical_data():
    try:
        time_range = request.args.get('range', '24h')
        
        # คำนวณช่วงเวลา
        now = datetime.now()
        if time_range == '1h':
            start_time = now - timedelta(hours=1)
        elif time_range == '24h':
            start_time = now - timedelta(hours=24)
        elif time_range == '7d':
            start_time = now - timedelta(days=7)
        elif time_range == '30d':
            start_time = now - timedelta(days=30)
        else:
            start_time = now - timedelta(hours=24)
        
        # ดึงข้อมูลจากฐานข้อมูล
        query = SensorData.query.filter(
            SensorData.timestamp >= start_time
        ).order_by(SensorData.timestamp.asc())
        
        data = query.all()
        
        # จัดรูปแบบข้อมูล
        result = [{
            'timestamp': record.timestamp.isoformat(),
            'temperature': record.temperature,
            'humidity': record.humidity,
            'tds': record.tds,
            'ph': record.ph,
            'ec': record.ec
        } for record in data]
        
        return jsonify({
            'status': 'success',
            'range': time_range,
            'data': result,
            'count': len(result)
        })
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
    
        

@api_bp.route('/sensor/all-sensor-data')
def get_all_sensor_data():
    data = SensorData.queryall( # type: ignore
        order_by=['timestamp', 'desc'],
        limit=100
    )
    
    result = [{
        'id': item.id,
        'temperature': item.temperature,
        'humidity': item.humidity,
        'tds': item.tds,
        'ph': item.ph,
        'ec': item.ec,
        'timestamp': item.timestamp.isoformat()
    } for item in data]
    
    return jsonify(result)
