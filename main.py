import sys
import os
import socket
import threading
from waitress import serve
from backend import create_app

def get_base_path():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))

BASE_DIR = get_base_path()
DATA_DIR = os.path.join(BASE_DIR, 'data')
DB_PATH = os.path.join(DATA_DIR, 'app_data.db')
MODEL_DIR = os.path.join(BASE_DIR, 'models')
MODEL_PATH = os.path.join(MODEL_DIR, 'mobile_facenet_112x112.onnx')

# Ensure directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(os.path.join(DATA_DIR, 'photos'), exist_ok=True)
os.makedirs(MODEL_DIR, exist_ok=True)

def start_server(app, host, port):
    print(f"🚀 OmniRoster Server running on http://{host}:{port}")
    serve(app, host=host, port=port, _quiet=True)

if __name__ == '__main__':
    app = create_app(DB_PATH, DATA_DIR, MODEL_PATH)
    is_codespaces = os.environ.get('CODESPACES') == 'true'

    if is_codespaces:
        # Run as web server for Codespaces
        start_server(app, host='0.0.0.0', port=5000)
    else:
        # Try to run as Desktop App
        try:
            import webview
            port = 5000
            server_thread = threading.Thread(target=start_server, args=(app, '127.0.0.1', port), daemon=True)
            server_thread.start()
            url = f"http://127.0.0.1:{port}"
            window = webview.create_window('OmniRoster Kiosk V2.5', url=url, width=1280, height=800)
            webview.start(func=None, window=window, debug=False)
        except ImportError:
            print("️ pywebview not found. Running in Web Mode...")
            start_server(app, host='0.0.0.0', port=5000)
