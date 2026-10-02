import os
from flask import Blueprint, render_template, jsonify, current_app, request
from backend.database import get_db_connection

main_routes = Blueprint('main', __name__)

@main_routes.route('/')
def index():
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

@main_routes.route('/workspace/<int:ws_id>')
def open_workspace(ws_id):
    db_path = current_app.config['DB_PATH']
    conn = get_db_connection(db_path)
    ws = conn.execute('SELECT * FROM workspaces WHERE id = ?', (ws_id,)).fetchone()
    conn.close()
    
    if not ws:
        return "Workspace not found", 404
        
    return render_template('roster_workspace.html', workspace=ws)

@main_routes.route('/api/workspace/<int:ws_id>/employees', methods=['GET'])
def get_employees(ws_id):
    db_path = current_app.config['DB_PATH']
    conn = get_db_connection(db_path)
    employees = conn.execute('SELECT * FROM staff WHERE workspace_id = ?', (ws_id,)).fetchall()
    conn.close()
    return jsonify([dict(e) for e in employees])

@main_routes.route('/api/workspace/<int:ws_id>/add_employee', methods=['POST'])
def add_employee(ws_id):
    name = request.form.get('name')
    role = request.form.get('role')
    photo = request.files.get('photo')

    if not name or not photo:
        return jsonify({"error": "Name and photo are required"}), 400

    # 1. Save the physical photo to the STATIC folder so the browser can see it
    static_dir = current_app.static_folder
    photos_dir = os.path.join(static_dir, 'photos')
    os.makedirs(photos_dir, exist_ok=True)
    
    safe_name = name.replace(' ', '_')
    filename = f"{ws_id}_{safe_name}_{photo.filename}"
    
    # The path the browser will use
    photo_path_browser = f"/static/photos/{filename}" 
    # The path the server uses to write the file
    full_photo_path = os.path.join(photos_dir, filename) 
    
    photo.save(full_photo_path)

    # 2. AI Extraction
    from backend.ai_service import extract_embedding
    embedding_bytes = extract_embedding(full_photo_path)
    
    if not embedding_bytes:
        os.remove(full_photo_path)
        return jsonify({"error": "Could not detect a face in the photo."}), 400

    # 3. Save to Database
    db_path = current_app.config['DB_PATH']
    conn = get_db_connection(db_path)
    conn.execute(
        "INSERT INTO staff (workspace_id, name, role, photo_path, face_embedding) VALUES (?, ?, ?, ?, ?)",
        (ws_id, name, role, photo_path_browser, embedding_bytes)
    )
    conn.commit()
    conn.close()

    return jsonify({"status": "success", "message": "Employee added!"}), 201
