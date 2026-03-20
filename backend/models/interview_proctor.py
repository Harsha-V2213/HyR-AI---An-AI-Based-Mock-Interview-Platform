import cv2
from deepface import DeepFace

def run_behavioral_analysis():
    
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    
    frame_counter = 0
    current_emotion = "Analyzing..."
    
    print("🎥 Starting Video Feed... (Press 'q' on the video window to stop)")

    while cap.isOpened():
        success, image = cap.read()
        if not success:
            break

        # Mirror the image for a natural selfie-view
        image = cv2.flip(image, 1)
        
        # OpenCV needs grayscale for the fast face detector
        gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # --- 1. EYE CONTACT & PRESENCE (OpenCV) ---
        faces = face_cascade.detectMultiScale(gray_image, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
        
        if len(faces) > 0:
            presence_status = "Face Detected (Good Eye Contact)"
            color = (0, 255, 0) # Green
            
            # Draw a box around the face
            for (x, y, w, h) in faces:
                cv2.rectangle(image, (x, y), (x+w, y+h), (255, 0, 0), 2)
        else:
            presence_status = "Face Lost! Look at the camera."
            color = (0, 0, 255) # Red

        # --- 2. EMOTION ANALYSIS (DeepFace) ---
        # DeepFace expects RGB colors
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Sample emotion every 30 frames to keep the video running smoothly
        if frame_counter % 30 == 0:
            try:
                analysis = DeepFace.analyze(rgb_image, actions=['emotion'], enforce_detection=False)
                current_emotion = analysis[0]['dominant_emotion']
            except Exception:
                pass
        
        frame_counter += 1

        # --- DISPLAY METRICS ON SCREEN ---
        cv2.putText(image, f"Emotion: {current_emotion.capitalize()}", (20, 40), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        cv2.putText(image, f"Status: {presence_status}", (20, 80), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

        cv2.imshow('AI Mock Interview Proctoring', image)

        # Press 'q' to break the loop
        if cv2.waitKey(5) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    run_behavioral_analysis()
