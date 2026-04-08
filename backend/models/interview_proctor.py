import cv2
import numpy as np
import time
from deepface import DeepFace

# --- SHARED BEHAVIORAL STATE ---
behavior_metrics = {"total_frames": 0, "eye_contact_frames": 0}
current_emotion = "Analyzing..."

def reset_behavior_metrics():
    global behavior_metrics, current_emotion
    behavior_metrics["total_frames"] = 0
    behavior_metrics["eye_contact_frames"] = 0
    current_emotion = "Analyzing..."

# --- INITIALIZE AI ---
# Load the Haar Cascade globally so it's ready instantly
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

def generate_video_frames():
    global behavior_metrics, current_emotion
    frame_counter = 0
    
    # 🚨 FIX: Camera is initialized INSIDE the generator so it only turns on 
    # when the frontend explicitly requests the video feed.
    camera = cv2.VideoCapture(0)
    
    # Give the camera hardware 1 second to warm up and focus
    time.sleep(1.0)
    
    try:
        while True:
            if not camera.isOpened():
                blank_frame = np.zeros((480, 640, 3), dtype=np.uint8)
                cv2.putText(blank_frame, "CAMERA UNAVAILABLE", (120, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                ret, buffer = cv2.imencode('.jpg', blank_frame)
                yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
                time.sleep(1)
                continue

            success, frame = camera.read()
            if not success: 
                break
                
            # Mirror the image for a natural selfie-view
            frame = cv2.flip(frame, 1)
            
            behavior_metrics["total_frames"] += 1
            frame_counter += 1
            
            # --- 1. EYE CONTACT & PRESENCE (OpenCV) ---
            gray_image = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray_image, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

            if len(faces) > 0:
                behavior_metrics["eye_contact_frames"] += 1
                presence_status = "Face Detected (Good Eye Contact)"
                color = (0, 255, 0) # Green
                
                # Draw a box around the face
                for (x, y, w, h) in faces:
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
            else:
                presence_status = "Face Lost! Look at the camera."
                color = (0, 0, 255) # Red

            # --- 2. EMOTION ANALYSIS (DeepFace) ---
            # Sample emotion every 30 frames to keep the video running smoothly
            if frame_counter % 30 == 0:
                rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                try:
                    # enforce_detection=False prevents crashes if the face is briefly lost
                    analysis = DeepFace.analyze(rgb_image, actions=['emotion'], enforce_detection=False)
                    current_emotion = analysis[0]['dominant_emotion']
                except Exception:
                    pass

            # --- DISPLAY METRICS ON WEB FEED ---
            cv2.putText(frame, f"Emotion: {current_emotion.capitalize()}", (20, 40), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            cv2.putText(frame, f"Status: {presence_status}", (20, 80), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
                    
            # Encode and send the frame to React
            ret, buffer = cv2.imencode('.jpg', frame)
            yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
            
    finally:
        # 🚨 FIX: Safely release the hardware and turn the light off when the stream ends
        camera.release()