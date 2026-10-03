import os
import cv2
import numpy as np
import onnxruntime as ort
import urllib.request

# A reliable, direct URL for the MobileFaceNet model
MODEL_URL = "https://github.com/leondgarse/Keras_insightface/releases/download/v1.0.0/mobile_facenet_112x112.onnx"

class FaceRecognitionService:
    def __init__(self, model_path):
        self.model_path = model_path
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.session = None
        
        # 1. Check if model exists and is valid (must be > 1MB to be a real model)
        needs_download = not os.path.exists(model_path) or os.path.getsize(model_path) < 1000000
        
        if needs_download:
            print(f"⚠️ Model missing or corrupt. Downloading fresh copy to {model_path}...")
            try:
                os.makedirs(os.path.dirname(model_path), exist_ok=True)
                urllib.request.urlretrieve(MODEL_URL, model_path)
                print("✅ Model downloaded successfully!")
            except Exception as e:
                print(f"❌ Failed to download model: {e}. Face recognition will be disabled.")
                return

        # 2. Load the model into ONNX Runtime
        try:
            self.session = ort.InferenceSession(model_path, providers=['CPUExecutionProvider'])
            print(f"✅ AI Model loaded successfully into memory.")
        except Exception as e:
            print(f"❌ AI Model file is corrupt. Error: {e}. Face recognition disabled.")
    
    def extract_embedding(self, image_path):
        """Extract facial embedding from an image file."""
        if not self.session:
            return None, "AI model not loaded"
        
        img = cv2.imread(image_path)
        if img is None:
            return None, "Could not read image"
        
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
        
        if len(faces) == 0:
            return None, "No face detected"
        
        (x, y, w, h) = faces[0]
        pad = 10
        x = max(0, x - pad)
        y = max(0, y - pad)
        w = min(img.shape[1] - x, w + 2 * pad)
        h = min(img.shape[0] - y, h + 2 * pad)
        
        face_crop = img[y:y+h, x:x+w]
        face_resized = cv2.resize(face_crop, (112, 112))
        
        face_rgb = cv2.cvtColor(face_resized, cv2.COLOR_BGR2RGB)
        face_normalized = (face_rgb.astype(np.float32) / 127.5) - 1.0
        input_tensor = np.expand_dims(face_normalized, axis=0)
        
        try:
            input_name = self.session.get_inputs()[0].name
            output = self.session.run(None, {input_name: input_tensor})
            embedding = output[0][0]
            embedding = embedding / np.linalg.norm(embedding)
            return embedding.tobytes(), "Success"
        except Exception as e:
            return None, f"AI inference error: {e}"
    
    def compare_embeddings(self, emb1_bytes, emb2_bytes, threshold=0.4):
        """Compare two facial embeddings."""
        if not emb1_bytes or not emb2_bytes:
            return False, 1.0
        
        try:
            vec1 = np.frombuffer(emb1_bytes, dtype=np.float32)
            vec2 = np.frombuffer(emb2_bytes, dtype=np.float32)
            
            similarity = np.dot(vec1, vec2)
            distance = 1.0 - similarity
            
            return distance < threshold, round(distance, 4)
        except:
            return False, 1.0
