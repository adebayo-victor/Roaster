import os
from deepface import DeepFace

def extract_face_embedding(image_path):
    """
    Uses DeepFace to detect the face in the image and extract its 128-d embedding.
    Returns the embedding as bytes for SQLite storage.
    """
    try:
        # enforce_detection=False prevents crashes if the photo is weird/blurry
        # model_name="Facenet" is lightweight and fast
        embedding_objs = DeepFace.represent(
            img_path=image_path, 
            model_name="Facenet", 
            enforce_detection=False,
            detector_backend="opencv" # Uses OpenCV for fast face detection
        )
        
        # DeepFace returns a list of faces found. We take the first one.
        if embedding_objs and len(embedding_objs) > 0:
            embedding_array = embedding_objs[0]["embedding"]
            # Convert the list of floats to bytes for SQLite BLOB storage
            import numpy as np
            return np.array(embedding_array).tobytes()
        else:
            return None
            
    except Exception as e:
        print(f"AI Extraction Error: {e}")
        return None

def compare_faces(embedding_bytes_1, embedding_bytes_2, threshold=0.4):
    """
    Compares two embeddings. Returns True if they match (same person).
    """
    import numpy as np
    if not embedding_bytes_1 or not embedding_bytes_2:
        return False
        
    arr1 = np.frombuffer(embedding_bytes_1, dtype=np.float32)
    arr2 = np.frombuffer(embedding_bytes_2, dtype=np.float32)
    
    # Calculate Cosine Similarity
    dot_product = np.dot(arr1, arr2)
    norm1 = np.linalg.norm(arr1)
    norm2 = np.linalg.norm(arr2)
    similarity = dot_product / (norm1 * norm2)
    
    # Higher similarity means closer match. Threshold is usually around 0.4 to 0.6
    return similarity > threshold
