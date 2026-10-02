from flask import Blueprint, render_template, jsonify, current_app, request
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

@main_routes.route('/api/workspace', methods=['POST'])
def create_workspace():
    """API endpoint to create a new Workspace (Folder)."""
    data = request.json
    name = data.get('name')
    folder_type = data.get('folder_type') # 'roster' or 'timetable'
    expected_time = data.get('expected_time')
    buffer_mins = data.get('buffer_mins')

    if not name or not folder_type:
        return jsonify({"error": "Name and folder type are required"}), 400

    db_path = current_app.config['DB_PATH']
    conn = get_db_connection(db_path)
    
    # Insert the new workspace into the database
    conn.execute(
        "INSERT INTO workspaces (name, folder_type, expected_time, buffer_mins) VALUES (?, ?, ?, ?)",
        (name, folder_type, expected_time, buffer_mins)
    )
    conn.commit()
    conn.close()

    return jsonify({"status": "success", "message": "Workspace created!"}), 201
