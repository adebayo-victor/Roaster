import os
import csv
import io
import base64
from datetime import datetime
from flask import Blueprint, render_template, jsonify, current_app, request, send_file
from backend.database import get_db_connection

main_routes = Blueprint('main', __name__)

@main_routes.route('/')
def index():
    db_path = current_app.config['DB_PATH']
    conn = get_db_connection(db_path)
    workspaces = conn.execute('SELECT * FROM workspaces ORDER BY created_at DESC').fetchall()
    
    ws_list = []
    today = datetime.now().strftime('%Y-%m-%d')
    for ws in workspaces:
        total_staff = conn.execute('SELECT COUNT(*) as c FROM staff WHERE workspace_id=?', (ws['id'],)).fetchone()['c']
        # Get today's stats
        logs = conn.execute('SELECT status FROM attendance_logs WHERE workspace_id=? AND date_str=?', (ws['id'], today)).fetchall()
        stats = {'on_time': 0, 'late': 0, 'pending': total_staff}
        for log in logs:
            if log['status'] == 'ON_TIME': stats['on_time'] += 1; stats['pending'] -= 1
            elif log['status'] == 'LATE': stats['late'] += 1; stats['pending'] -= 1
            
        ws_list.append({**dict(ws), 'total_staff': total_staff, 'stats': stats})
        
    conn.close()
    return render_template('index.html', workspaces=ws_list)

@main_routes.route('/kiosk/<int:ws_id>')
def open_kiosk(ws_id):
    db_path = current_app.config['DB_PATH']
    conn = get_db_connection(db_path)
    ws = conn.execute('SELECT * FROM workspaces WHERE id = ?', (ws_id,)).fetchone()
    if not ws: return "Not found", 404
    
    today = datetime.now().strftime('%Y-%m-%d')
    staff = conn.execute('SELECT * FROM staff WHERE workspace_id = ?', (ws_id,)).fetchall()
    
    staff_list = []
    for s in staff:
        log = conn.execute('SELECT status FROM attendance_logs WHERE staff_id=? AND date_str=?', (s['id'], today)).fetchone()
        status = log['status'] if log else 'PENDING'
        staff_list.append({**dict(s), 'current_status': status})
        
    conn.close()
    return render_template('kiosk.html', workspace=dict(ws), staff=staff_list)

@main_routes.route('/admin/<int:ws_id>')
def open_admin(ws_id):
    db_path = current_app.config['DB_PATH']
    conn = get_db_connection(db_path)
    ws = conn.execute('SELECT * FROM workspaces WHERE id = ?', (ws_id,)).fetchone()
    conn.close()
    if not ws: return "Not found", 404
    return render_template('admin.html', workspace=dict(ws))

# --- API ENDPOINTS ---

@main_routes.route('/api/workspace', methods=['POST'])
def create_workspace():
    data = request.json
    db_path = current_app.config['DB_PATH']
    conn = get_db_connection(db_path)
    conn.execute(
        "INSERT INTO workspaces (name, folder_type, shift_start, shift_end, grace_mins, custom_property_title) VALUES (?, ?, ?, ?, ?, ?)",
        (data['name'], 'roster', data.get('shift_start', '09:00'), data.get('shift_end', '17:00'), int(data.get('grace_mins', 10)), data.get('custom_prop', 'Station'))
    )
    conn.commit(); conn.close()
    return jsonify({"status": "success"}), 201

@main_routes.route('/api/workspace/<int:ws_id>/staff', methods=['POST'])
def add_staff(ws_id):
    name = request.form.get('name')
    pin = request.form.get('pin')
    station = request.form.get('station')
    photo = request.files.get('photo')

    if not name or not photo: return jsonify({"error": "Name and photo required"}), 400

    static_dir = current_app.static_folder
    photos_dir = os.path.join(static_dir, 'photos')
    os.makedirs(photos_dir, exist_ok=True)
    
    filename = f"{ws_id}_{name.replace(' ', '_')}_{photo.filename}"
    full_path = os.path.join(photos_dir, filename)
    browser_path = f"/static/photos/{filename}"
    photo.save(full_path)

    # AI Extraction
    ai_service = current_app.config['AI_SERVICE']
    embedding_bytes, msg = ai_service.extract_embedding(full_path)
    
    db_path = current_app.config['DB_PATH']
    conn = get_db_connection(db_path)
    conn.execute(
        "INSERT INTO staff (workspace_id, name, pin_code, station, photo_path, face_embedding) VALUES (?, ?, ?, ?, ?, ?)",
        (ws_id, name, pin, station, browser_path, embedding_bytes)
    )
    conn.commit(); conn.close()
    return jsonify({"status": "success", "ai_msg": msg}), 201

@main_routes.route('/api/kiosk/checkin', methods=['POST'])
def kiosk_checkin():
    data = request.json
    ws_id = data.get('ws_id')
    pin = data.get('pin')
    live_image_b64 = data.get('image') # Base64 from webcam
    
    db_path = current_app.config['DB_PATH']
    conn = get_db_connection(db_path)
    
    staff = conn.execute('SELECT * FROM staff WHERE workspace_id=? AND pin_code=?', (ws_id, pin)).fetchone()
    if not staff:
        conn.close()
        return jsonify({"error": "Invalid PIN"}), 404
        
    # Face Verification (Optional)
    face_verified = False
    distance = 1.0
    if live_image_b64 and staff['face_embedding']:
        try:
            header, encoded = live_image_b64.split(",", 1)
            binary_data = base64.b64decode(encoded)
            temp_path = os.path.join(current_app.config['DATA_DIR'], 'temp_checkin.jpg')
            with open(temp_path, 'wb') as f: f.write(binary_data)
            
            ai_service = current_app.config['AI_SERVICE']
            live_emb, _ = ai_service.extract_embedding(temp_path)
            if live_emb:
                face_verified, distance = ai_service.compare_embeddings(staff['face_embedding'], live_emb)
            os.remove(temp_path)
        except Exception as e:
            print(f"Face check error: {e}")

    # Time Logic
    now = datetime.now()
    today_str = now.strftime('%Y-%m-%d')
    time_str = now.strftime('%H:%M:%S')
    
    existing = conn.execute('SELECT * FROM attendance_logs WHERE staff_id=? AND date_str=?', (staff['id'], today_str)).fetchone()
    if existing:
        conn.close()
        return jsonify({"message": "Already checked in", "status": existing['status']}), 200

    ws = conn.execute('SELECT * FROM workspaces WHERE id=?', (ws_id,)).fetchone()
    expected_time = datetime.strptime(f"{today_str} {ws['shift_start']}", '%Y-%m-%d %H:%M')
    grace_limit = expected_time.replace(minute=expected_time.minute + ws['grace_mins'])
    
    status = "ON_TIME"
    if now > grace_limit: status = "LATE"
    elif now < expected_time: status = "EARLY"

    method = "PIN"
    if face_verified: method += " + FACE"
    
    conn.execute(
        "INSERT INTO attendance_logs (staff_id, workspace_id, date_str, clock_in_time, status, method) VALUES (?, ?, ?, ?, ?, ?)",
        (staff['id'], ws_id, today_str, time_str, status, method)
    )
    conn.commit(); conn.close()
    
    return jsonify({
        "status": "success", 
        "name": staff['name'], 
        "verified_status": status,
        "face_match": face_verified,
        "distance": round(distance, 2)
    }), 200

@main_routes.route('/api/admin/logs/<int:ws_id>')
def get_logs(ws_id):
    db_path = current_app.config['DB_PATH']
    conn = get_db_connection(db_path)
    logs = conn.execute('''
        SELECT a.*, s.name as staff_name, s.station, w.name as ws_name 
        FROM attendance_logs a 
        JOIN staff s ON a.staff_id = s.id 
        JOIN workspaces w ON a.workspace_id = w.id
        WHERE a.workspace_id = ? ORDER BY a.clock_in_time DESC
    ''', (ws_id,)).fetchall()
    conn.close()
    return jsonify([dict(l) for l in logs])

@main_routes.route('/api/admin/export/<int:ws_id>')
def export_csv(ws_id):
    db_path = current_app.config['DB_PATH']
    conn = get_db_connection(db_path)
    logs = conn.execute('''
        SELECT a.date_str, a.clock_in_time, s.name, s.station, a.status, a.method
        FROM attendance_logs a JOIN staff s ON a.staff_id = s.id
        WHERE a.workspace_id = ? ORDER BY a.date_str DESC
    ''', (ws_id,)).fetchall()
    conn.close()
    
    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow(['Date', 'Time', 'Name', 'Station', 'Status', 'Method'])
    for row in logs: cw.writerow(row.values())
    
    output = si.getvalue()
    return send_file(io.BytesIO(output.encode()), mimetype='text/csv', as_attachment=True, download_name=f'attendance_{ws_id}.csv')
