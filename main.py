import sys
import os
import socket
import threading
from waitress import serve
import webview

# Import the Flask app factory
from backend import create_app

# ==========================================
# 1. DYNAMIC PATH RESOLUTION
# ==========================================
def get_base_path():
    """
    Figures out if we are running in development (python main.py) 
    or packaged as an .exe (PyInstaller).
    """
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))

BASE_DIR = get_base_path()
DATA_DIR = os.path.join(BASE_DIR, 'data')
DB_PATH = os.path.join(DATA_DIR, 'app_data.db')

# Ensure the data folder exists locally
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(os.path.join(DATA_DIR, 'photos'), exist_ok=True)

# ==========================================
# 2. SERVER & WINDOW LOGIC
# ==========================================
def find_free_port():
    """Finds a random available port on localhost to avoid conflicts."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        return s.getsockname()[1]

def start_server(app, port):
    """Starts the production-ready Waitress server."""
    serve(app, host='127.0.0.1', port=port, _quiet=True)

if __name__ == '__main__':
    # 1. Initialize Flask App
        app = create_app(DB_PATH, DATA_DIR)

    # 2. Find a free port and start Flask in a background thread
    port = find_free_port()
    print(f"🚀 Starting local server on http://127.0.0.1:{port}")
    
    server_thread = threading.Thread(target=start_server, args=(app, port), daemon=True)
    server_thread.start()
    
    # 3. Create the native Windows Window
    url = f"http://127.0.0.1:{port}"
    window = webview.create_window(
        'Smart Workforce Manager', 
        url=url, 
        width=1200, 
        height=800,
        resizable=True,
        min_size=(800, 600)
    )
    
    # 4. Start the GUI event loop
    webview.start(func=None, window=window, debug=False)
