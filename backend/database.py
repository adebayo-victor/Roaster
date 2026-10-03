import sqlite3

def get_db_connection(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row 
    return conn

def init_db(db_path):
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS workspaces (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            folder_type TEXT NOT NULL DEFAULT 'roster', 
            shift_start TEXT DEFAULT '09:00',        
            shift_end TEXT DEFAULT '17:00',
            grace_mins INTEGER DEFAULT 10,
            custom_property_title TEXT DEFAULT 'Station / Table No',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS staff (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            workspace_id INTEGER,
            name TEXT NOT NULL,
            pin_code TEXT,
            station TEXT,
            photo_path TEXT,
            face_embedding BLOB,       
            FOREIGN KEY(workspace_id) REFERENCES workspaces(id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS attendance_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            staff_id INTEGER,
            workspace_id INTEGER,
            date_str TEXT,             
            clock_in_time TEXT,        
            status TEXT,
            method TEXT,
            photo_proof_path TEXT,
            FOREIGN KEY(staff_id) REFERENCES staff(id)
        )
    ''')

    conn.commit()
    conn.close()
    print(f"✅ Database initialized at: {db_path}")
