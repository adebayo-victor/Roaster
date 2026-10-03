import os
import sys
from flask import Flask

def create_app(db_path, data_dir, model_path):
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    app = Flask(__name__,
                template_folder=os.path.join(base_path, 'templates'),
                static_folder=os.path.join(base_path, 'static'))

    app.config['DB_PATH'] = db_path
    app.config['DATA_DIR'] = data_dir
    app.config['MODEL_PATH'] = model_path
    app.config['SECRET_KEY'] = 'omniroster-secret-key-2026' 

    # Initialize AI Service
    from backend.ai_service import FaceRecognitionService
    app.config['AI_SERVICE'] = FaceRecognitionService(model_path)

    from backend.routes import main_routes
    app.register_blueprint(main_routes)

    from backend.database import init_db
    with app.app_context():
        init_db(db_path)

    return app
