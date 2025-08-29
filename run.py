from app import create_app, db
import os

app = create_app()

with app.app_context():
    from core import models  # สำคัญ: ต้อง import หลังจาก create_app
    db.create_all()
    '''
    print("✅ Database created at:", app.config["SQLALCHEMY_DATABASE_URI"])
    print("✅ Tables:", db.metadata.tables)
    
    print("DB URI:", app.config['SQLALCHEMY_DATABASE_URI'])
    print("Resolved Path:", os.path.abspath(app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')))
    '''
if __name__ == '__main__':
    # ปิด reloader เพื่อไม่ให้ Flask เปิด COM4 ซ้ำ
    app.run(debug=True, use_reloader=False)
    