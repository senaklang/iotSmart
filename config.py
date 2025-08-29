import os

class Config:
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    INSTANCE_DIR = os.path.join(BASE_DIR, 'instance')
    os.makedirs(INSTANCE_DIR, exist_ok=True)

    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(INSTANCE_DIR, 'sensor_data.db')
    SQLALCHEMY_BINDS = {
        'lamp': 'sqlite:///' + os.path.join(INSTANCE_DIR, 'lamp.db')
    }

    SQLALCHEMY_TRACK_MODIFICATIONS = False