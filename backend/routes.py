from flask import Blueprint, render_template, jsonify, current_app
from backend.database import get_db_connection

main_routes = Blueprint('main', __name__)

@main_routes.route('/')
def index():
    """The main dashboard showing the 'Folders'."""
    db_path = current_app.config['DB_PATH']
    conn = get_db_connection(db_path)
    
    # Fetch existing workspaces
    workspaces = conn.execute('SELECT * FROM workspaces ORDER BY created_at DESC').fetchall()
    conn.close()
    
    return render_template('index.html', workspaces=workspaces)

@main_routes.route('/api/health')
def health_check():
    return jsonify({"status": "online", "message": "Local server is running!"})
