from flask import Flask, render_template, Response, jsonify
import cv2
import threading
import time
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

app = Flask(__name__)

# --- GLOBAL STATE ---
ai_state = {
    "status": "Ready.",
    "current_question": "Click 'Start Interview' to begin reading resume.",
    "latest_score": "--",
    "questions": [],
    "current_q_index": 0,
    "is_busy": False
}

semantic_scores = []
behavior_metrics = {
    "total_frames": 0,
    "eye_contact_frames": 0,
    "anxiety_frames": 0
}
current_emotion = "Neutral"
frame_for_analysis = None

# --- NEW: TEMPORAL SMOOTHING CACHE ---
last_known_face = None
face_lost_counter = 0

# --- BACKGROUND WORKERS ---

def emotion_worker_thread():
    global frame_for_analysis, current_emotion, behavior_metrics
    from deepface import DeepFace
    
    while True:
        if frame_for_analysis is not None:
            try:
                analysis = DeepFace.analyze(frame_for_analysis, actions=['emotion'], enforce_detection=False)
                current_emotion = analysis[0]['dominant_emotion']
                if current_emotion in ['fear', 'sad', 'angry']:
                    behavior_metrics["anxiety_frames"] += 1
            except:
                pass
            frame_for_analysis = None
        time.sleep(0.5)

def background_mistral_worker():
    global ai_state
    try:
        ai_state["status"] = "Reading Resume..."
        from backend.models.resume_parser import parse_resume
        
        parsed_data = parse_resume("sample_resume.pdf") 
        if "error" in parsed_data:
            ai_state["current_question"] = "Error reading resume file."
            ai_state["status"] = "Failed."
            ai_state["is_busy"] = False
            return

        ai_state["status"] = "Mistral generating personalized questions..."
        from backend.models.question_generator import generate_questions
        questions = generate_questions(parsed_data, "Software Engineer", 3)
        
        if questions and "Error" not in questions[0]:
            ai_state["questions"] = questions
            ai_state["current_question"] = questions[0]
            ai_state["status"] = "Waiting for you... (Click button to answer Question 1)"
        else:
            ai_state["current_question"] = "Error generating questions."
            ai_state["status"] = "Failed."
            
    except Exception as e:
        print(f"Error loading AI: {e}")
        ai_state["current_question"] = "System Error. Check terminal logs."
        ai_state["status"] = "Failed."
        
    ai_state["is_busy"] = False

def background_answer_worker(question_text):
    global ai_state, semantic_scores, behavior_metrics
    try:
        from backend.models.speech_analyzer import transcribe_audio_from_mic, evaluate_semantics
        
        ai_state["status"] = "🎤 Listening... (Speak your answer into the mic!)"
        user_transcript = transcribe_audio_from_mic()
        
        if "Error:" not in user_transcript and "Could not request results" not in user_transcript:
            ai_state["status"] = "🧠 Transcribed! Running SentenceBERT grading..."
            
            raw_score = evaluate_semantics(user_transcript, question_text)
            score = float(raw_score)
            
            semantic_scores.append(score)
            ai_state["latest_score"] = round(score, 1)
            ai_state["status"] = f"✅ Answer Graded: {round(score, 1)}%. Click Next."
        else:
            ai_state["status"] = "⚠️ Could not hear you clearly. Please try again."
            semantic_scores.append(0.0) 
            
        ai_state["current_q_index"] += 1
        
        if ai_state["current_q_index"] < len(ai_state["questions"]):
             ai_state["current_question"] = ai_state["questions"][ai_state["current_q_index"]]
        else:
            ai_state["status"] = "Calculating Final CRI..."
            time.sleep(1) 
            
            avg_semantic = float(sum(semantic_scores) / len(semantic_scores) if semantic_scores else 0.0)
            frames = float(behavior_metrics["total_frames"])
            
            eye_contact_ratio = float(behavior_metrics["eye_contact_frames"] / frames if frames > 0 else 0.0)
            anxiety_ratio = float(behavior_metrics["anxiety_frames"] / (frames / 30.0) if frames > 0 else 0.0)
            
            calm_ratio = max(0.0, 1.0 - anxiety_ratio)
            behavior_score = float(((eye_contact_ratio * 0.5) + (calm_ratio * 0.5)) * 100)
            
            cri = float((0.6 * avg_semantic) + (0.4 * behavior_score))
            
            ai_state["current_question"] = f"🏆 FINAL CRI: {round(cri, 1)}/100 \n(Tech: {round(avg_semantic, 1)} | Behavior: {round(behavior_score, 1)})"
            ai_state["status"] = "🏁 Interview Complete!"
            
    except Exception as e:
        print(f"Scoring Error: {e}")
        ai_state["status"] = "❌ Error processing audio."
        
    ai_state["is_busy"] = False


# --- WEB STREAM GENERATOR WITH TEMPORAL SMOOTHING ---

def generate_video_frames():
    global behavior_metrics, frame_for_analysis, current_emotion, last_known_face, face_lost_counter
    
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

    while cap.isOpened():
        success, frame = cap.read()
        if not success: 
            break
        
        frame = cv2.flip(frame, 1)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        behavior_metrics["total_frames"] += 1
        
        # More aggressive scaling to find faces easier
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(60, 60))
        
        current_face = None
        
        # If we found faces, grab the biggest one
        if len(faces) > 0:
            # Sort by area (w*h) to get the largest face in the frame
            faces = sorted(faces, key=lambda x: x[2]*x[3], reverse=True)
            current_face = faces[0]
            face_lost_counter = 0
            behavior_metrics["eye_contact_frames"] += 1
        else:
            # We lost the face! Use the cache if it hasn't been too long.
            face_lost_counter += 1
            if last_known_face is not None and face_lost_counter < 15: # Remember for half a second
                current_face = last_known_face
                behavior_metrics["eye_contact_frames"] += 1

        # --- THE TEMPORAL SMOOTHING MATH ---
        if current_face is not None:
            x, y, w, h = current_face
            
            # If we have a history, smoothly glide the box using Exponential Moving Average
            if last_known_face is not None:
                lx, ly, lw, lh = last_known_face
                alpha = 0.3 # Smoothing factor (lower = smoother but slightly delayed)
                x = int(lx + alpha * (x - lx))
                y = int(ly + alpha * (y - ly))
                w = int(lw + alpha * (w - lw))
                h = int(lh + alpha * (h - lh))
                
            last_known_face = (x, y, w, h)
            
            # Draw the smoothed box
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 100), 2)
            cv2.putText(frame, f"Emotion: {current_emotion.capitalize()}", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

            # --- THE CROP UPGRADE ---
            # Send ONLY the isolated face to DeepFace once per second
            if behavior_metrics["total_frames"] % 30 == 0:
                face_crop = cv2.cvtColor(frame[y:y+h, x:x+w], cv2.COLOR_BGR2RGB)
                if face_crop.size > 0:
                    frame_for_analysis = face_crop
        else:
            # We completely lost the face for too long. Clear the cache.
            last_known_face = None
            cv2.putText(frame, "⚠️ Look at the camera!", (20, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        ret, buffer = cv2.imencode('.jpg', frame)
        yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')

    cap.release()

# --- WEB ROUTES ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(generate_video_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/get_status', methods=['GET'])
def get_status():
    return jsonify(ai_state)

@app.route('/next_action', methods=['POST'])
def next_action():
    global ai_state
    
    if ai_state["is_busy"]:
        return jsonify({"success": False, "message": "System is busy."})

    if not ai_state["questions"]:
        ai_state["is_busy"] = True
        ai_state["status"] = "Initializing AI Brain..."
        threading.Thread(target=background_mistral_worker).start()
        return jsonify({"success": True})
        
    if ai_state["questions"]:
        if ai_state["current_q_index"] >= len(ai_state["questions"]):
             return jsonify({"success": False, "message": "Interview is complete."})

        ai_state["is_busy"] = True
        current_q_text = ai_state["questions"][ai_state["current_q_index"]]
        threading.Thread(target=background_answer_worker, args=(current_q_text,)).start()
        
        return jsonify({"success": True})

if __name__ == '__main__':
    print("🚀 Starting Web Server on http://127.0.0.1:5000")
    threading.Thread(target=emotion_worker_thread, daemon=True).start()
    app.run(debug=True, threaded=True)