# app/__init__.py
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import Config
from core.hardware_interface import HardwareInterface
from flask_cors import CORS

db = SQLAlchemy()

def register_blueprints(app):
    """Register all Flask blueprints for the app."""
    from app.routes.index import index_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.sensor import sensor_bp
    from app.routes.api import api_bp
    from app.routes.apihtml import apihtml_bp
    from app.routes.hardware_api import hardware_bp

    blueprints = [
        index_bp,
        dashboard_bp,
        sensor_bp,
        api_bp,
        apihtml_bp,
        hardware_bp
    ]

    for bp in blueprints:
        app.register_blueprint(bp)

def create_app(config_class=Config):
    """Application factory."""
    app = Flask(__name__)
    CORS(app)
    app.config.from_object(config_class)

    # set template & static folders
    app.template_folder = os.path.join(app.root_path, '../templates')
    app.static_folder = os.path.join(app.root_path, '../static')

    if not os.path.exists(app.instance_path):
        os.makedirs(app.instance_path)

    # init database
    db.init_app(app)

    
    # register blueprints
    register_blueprints(app)
    
    # create hardware interface instance and connect
    
    
    hw = HardwareInterface(port='COM5')  # ปรับพอร์ตตามเครื่อง
    if hw.connect_serial():
        app.logger.info("HardwareInterface connected")
    else:
        app.logger.warning("HardwareInterface not connected (will retry)")
    app.config['hardware_interface'] = hw
    
    return app
