import cv2
import numpy as np
import base64
from deepface import DeepFace

# Load the Haar Cascade globally
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

# Shared state to calculate the final score
behavior_metrics = {"total_frames": 0, "eye_contact_frames": 0}

def reset_behavior_metrics():
    global behavior_metrics
    behavior_metrics["total_frames"] = 0
    behavior_metrics["eye_contact_frames"] = 0

def analyze_video_frame(base64_image_string, frame_counter):
    """
    Receives a base64 encoded image string from React over the internet,
    decodes it, runs OpenCV/DeepFace, and returns the metrics.
    """
    global behavior_metrics
    behavior_metrics["total_frames"] += 1
    
    # 1. Strip the "data:image/jpeg;base64," prefix from the string
    encoded_data = base64_image_string.split(',')[1]
    
    # 2. Convert base64 back into an OpenCV Image
    nparr = np.frombuffer(base64.b64decode(encoded_data), np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    presence_status = "Face Lost! Look at the camera."
    current_emotion = None

    # --- 1. EYE CONTACT (OpenCV) ---
    gray_image = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray_image, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

    if len(faces) > 0:
        behavior_metrics["eye_contact_frames"] += 1
        presence_status = "Face Detected (Good Eye Contact)"

    # --- 2. EMOTION ANALYSIS (DeepFace) ---
    # To save server costs, we only run DeepFace on every 30th frame sent by React
    if frame_counter % 30 == 0:
        rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        try:
            analysis = DeepFace.analyze(rgb_image, actions=['emotion'], enforce_detection=False)
            current_emotion = analysis[0]['dominant_emotion']
        except Exception:
            pass

    return {
        "status": presence_status,
        "emotion": current_emotion
    }