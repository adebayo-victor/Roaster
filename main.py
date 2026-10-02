import sys
import os
import socket
import threading
from waitress import serve
from backend import create_app

# ==========================================
# 1. DYNAMIC PATH RESOLUTION
# ==========================================
def get_base_path():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))

BASE_DIR = get_base_path()
DATA_DIR = os.path.join(BASE_DIR, 'data')
DB_PATH = os.path.join(DATA_DIR, 'app_data.db')

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(os.path.join(DATA_DIR, 'photos'), exist_ok=True)

# ==========================================
# 2. SERVER LOGIC
# ==========================================
def find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        return s.getsockname()[1]

def start_server(app, host, port):
    print(f" Server running on http://{host}:{port}")
    serve(app, host=host, port=port, _quiet=True)

if __name__ == '__main__':
    app = create_app(DB_PATH, DATA_DIR)

    # Check if we are in Codespaces (Headless environment)
    is_codespaces = os.environ.get('CODESPACES') == 'true'

    if is_codespaces:
        # Run as a standard web server for Codespaces
        # Codespaces will automatically forward port 5000
        start_server(app, host='0.0.0.0', port=5000)
    else:
        # Try to run as a Desktop App (for your local Windows PC later)
        try:
            import webview
            
            port = find_free_port()
            server_thread = threading.Thread(target=start_server, args=(app, '127.0.0.1', port), daemon=True)
            server_thread.start()
            
            url = f"http://127.0.0.1:{port}"
            window = webview.create_window('Smart Workforce Manager', url=url, width=1200, height=800)
            webview.start(func=None, window=window, debug=False)
            
        except ImportError:
            # Fallback if pywebview is not installed
            print("pywebview not found. Running in Web Mode...")
            start_server(app, host='0.0.0.0', port=5000)
