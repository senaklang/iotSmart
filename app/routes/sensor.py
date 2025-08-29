from flask import Blueprint, render_template, request
from core.models import SensorData
from datetime import datetime, timedelta
import pandas as pd

sensor_bp = Blueprint('sensor', __name__)

@sensor_bp.route('/sensor_history')
def history():
    data = SensorData.query.order_by(SensorData.timestamp.desc()).limit(10).all()
    return render_template('history.html', history=data)

@sensor_bp.route('/sensor_charts')
def charts():
    time_range = request.args.get('range', '48h')
    delta = {
        '48h': timedelta(hours=48),
        '7d': timedelta(days=7),
        '30d': timedelta(days=30)
    }.get(time_range, None)

    query = SensorData.query
    if delta:
        start = datetime.now() - delta
        query = query.filter(SensorData.timestamp >= start)

    data = query.order_by(SensorData.timestamp).all()
    df = pd.DataFrame([{
        'timestamp': d.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
        'temperature': d.temperature,
        'humidity': d.humidity,
        'tds': d.tds,
        'ph': d.ph
    } for d in data])

    summary = {
        'avg_temp': df['temperature'].mean() if not df.empty else 0,
        'avg_humidity': df['humidity'].mean() if not df.empty else 0,
        'avg_tds': df['tds'].mean() if not df.empty else 0,
        'avg_ph': df['ph'].mean() if not df.empty else 0
    }

    return render_template('sensor_charts.html',
                           sensor_data=df.to_dict(orient='list'),
                           summary_stats=summary)