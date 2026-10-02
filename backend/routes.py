import os
from flask import Blueprint, render_template, jsonify, current_app, request
from backend.database import get_db_connection

main_routes = Blueprint('main', __name__)

@main_routes.route('/')
def index():
    """The main dashboard showing the 'Folders'."""
    db_path = current_app.config['DB_PATH']
    conn = get_db_connection(db_path)
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
    folder_type = data.get('folder_type')
    expected_time = data.get('expected_time')
    buffer_mins = data.get('buffer_mins')

    if not name or not folder_type:
        return jsonify({"error": "Name and folder type are required"}), 400

    db_path = current_app.config['DB_PATH']
    conn = get_db_connection(db_path)
    conn.execute(
        "INSERT INTO workspaces (name, folder_type, expected_time, buffer_mins) VALUES (?, ?, ?, ?)",
        (name, folder_type, expected_time, buffer_mins)
    )
    conn.commit()
    conn.close()
    return jsonify({"status": "success", "message": "Workspace created!"}), 201

# ==========================================
# NEW ROUTES FOR BATCH 3
# ==========================================

@main_routes.route('/workspace/<int:ws_id>')
def open_workspace(ws_id):
    """Renders the inside of a specific workspace."""
    db_path = current_app.config['DB_PATH']
    conn = get_db_connection(db_path)
    ws = conn.execute('SELECT * FROM workspaces WHERE id = ?', (ws_id,)).fetchone()
    conn.close()
    
    if not ws:
        return "Workspace not found", 404
        
    return render_template('roster_workspace.html', workspace=ws)

@main_routes.route('/api/workspace/<int:ws_id>/employees', methods=['GET'])
def get_employees(ws_id):
    """Fetches all employees for a specific workspace."""
    db_path = current_app.config['DB_PATH']
    conn = get_db_connection(db_path)
    employees = conn.execute('SELECT * FROM staff WHERE workspace_id = ?', (ws_id,)).fetchall()
    conn.close()
    return jsonify([dict(e) for e in employees])

@main_routes.route('/api/workspace/<int:ws_id>/add_employee', methods=['POST'])
def add_employee(ws_id):
    """Handles adding a new employee and their photo."""
    name = request.form.get('name')
    role = request.form.get('role')
    photo = request.files.get('photo')

    if not name or not photo:
        return jsonify({"error": "Name and photo are required"}), 400

    # 1. Save the physical photo to the data/photos directory
    data_dir = current_app.config['DATA_DIR']
    photos_dir = os.path.join(data_dir, 'photos')
    os.makedirs(photos_dir, exist_ok=True)
    
    # Create a unique filename
    safe_name = name.replace(' ', '_')
    filename = f"{ws_id}_{safe_name}_{photo.filename}"
    photo_path = os.path.join(photos_dir, filename)
    photo.save(photo_path)

    # 2. AI Extraction Placeholder
    # In Batch 4, we will replace this with the actual ONNX model extraction.
    # For now, we generate 128 random bytes to prove the database pipeline works.
    import os as os_lib
    dummy_embedding = os_lib.urandom(128) 

    # 3. Save to Database
    db_path = current_app.config['DB_PATH']
    conn = get_db_connection(db_path)
    conn.execute(
        "INSERT INTO staff (workspace_id, name, role, photo_path, face_embedding) VALUES (?, ?, ?, ?, ?)",
        (ws_id, name, role, photo_path, dummy_embedding)
    )
    conn.commit()
    conn.close()

    return jsonify({"status": "success", "message": "Employee added!"}), 201
