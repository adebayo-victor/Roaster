import sqlite3

def get_db_connection(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row 
    return conn

def init_db(db_path):
    """Creates the tables if they don't exist yet."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    # 1. Workspaces (The "Folders")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS workspaces (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            folder_type TEXT NOT NULL, 
            expected_time TEXT,        
            buffer_mins INTEGER,       
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 2. Staff / Employees
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS staff (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            workspace_id INTEGER,
            name TEXT NOT NULL,
            role TEXT,
            photo_path TEXT,
            face_embedding BLOB,       
            constraints_json TEXT,     
            FOREIGN KEY(workspace_id) REFERENCES workspaces(id)
        )
    ''')

    # 3. Attendance Logs (For ROSTER folders)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS attendance_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            staff_id INTEGER,
            workspace_id INTEGER,
            date_str TEXT,             
            clock_in_time TEXT,        
            status TEXT,               
            FOREIGN KEY(staff_id) REFERENCES staff(id)
        )
    ''')

    # 4. Timetable Shifts (For TIMETABLE folders)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS timetable_shifts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            workspace_id INTEGER,
            date_str TEXT,
            shift_type TEXT,           
            assigned_staff_ids TEXT,   
            is_locked BOOLEAN DEFAULT 0 
        )
    ''')

    conn.commit()
    conn.close()
    print(f"✅ Database initialized at: {db_path}")
