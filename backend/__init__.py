import os
import sys
from flask import Flask

def create_app(db_path, data_dir):
    # Determine where the 'templates' and 'static' folders are
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    app = Flask(__name__,
                template_folder=os.path.join(base_path, 'templates'),
                static_folder=os.path.join(base_path, 'static'))

    # Store paths in the app config
    app.config['DB_PATH'] = db_path
    app.config['DATA_DIR'] = data_dir
    app.config['SECRET_KEY'] = 'super-secret-local-key' 

    # Import and register routes
    from backend.routes import main_routes
    app.register_blueprint(main_routes)

    # Initialize the database tables on startup
    from backend.database import init_db
    with app.app_context():
        init_db(db_path)

    return app
