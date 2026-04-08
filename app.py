from flask import Flask, Response, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, auth
from functools import wraps
import cv2
import threading
import time
import sys
import os
import numpy as np
from datetime import datetime

# Load environment variables and path
load_dotenv()
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from backend.models.resume_parser import parse_resume
from backend.models.question_generator import generate_questions
from backend.models.speech_analyzer import start_recording_mic, stop_recording_mic, evaluate_semantics

# Initialize Flask App & DB
app = Flask(__name__)
CORS(app) 

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
#app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'connect_args': {'check_same_thread': False}}
db = SQLAlchemy(app)

# Initialize Firebase Admin
try:
    cred = credentials.Certificate("firebase-key.json")
    firebase_admin.initialize_app(cred)
    print("✅ Firebase Admin Active")
except Exception as e:
    print(f"⚠️ Firebase Error: {e}")

# Database Model
class InterviewSession(db.Model):
    __tablename__ = 'interview_sessions'
    id = db.Column(db.Integer, primary_key=True)
    firebase_uid = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(150), nullable=False)
    semantic_score = db.Column(db.Float, nullable=False)
    behavioral_score = db.Column(db.Float, nullable=False)
    overall_cri = db.Column(db.Float, nullable=False)
    date_completed = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id, 
            "role": self.role, 
            "overall_cri": round(self.overall_cri, 1),
            "date": self.date_completed.isoformat()
        }

with app.app_context():
    db.create_all()

# Authentication Decorator
def firebase_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Unauthorized'}), 401
        token = auth_header.split(' ')[1]
        try:
            decoded_token = auth.verify_id_token(token)
            request.user_id = decoded_token['uid'] 
        except:
            return jsonify({'error': 'Invalid token'}), 401
        return f(*args, **kwargs)
    return decorated_function

# Global State Management
ai_state = {
    "status": "Ready.", 
    "current_state": "IDLE", 
    "current_question": "Waiting...",
    "questions": [], 
    "current_q_index": 0, 
    "is_busy": False, 
    "target_role": "", 
    "active_user_uid": None
}

semantic_scores = []
behavior_metrics = {"total_frames": 0, "eye_contact_frames": 0}

# Initialize Camera
camera = cv2.VideoCapture(0)

# --- WORKER FUNCTIONS ---

def generate_video_frames():
    global behavior_metrics
    while True:
        # Fail-safe: If camera is locked or disconnected, show an error frame instead of crashing (404 fix)
        if not camera.isOpened():
            blank_frame = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.putText(blank_frame, "CAMERA UNAVAILABLE", (120, 240), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            ret, buffer = cv2.imencode('.jpg', blank_frame)
            yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
            time.sleep(1)
            continue

        success, frame = camera.read()
        if not success:
            break
            
        behavior_metrics["total_frames"] += 1
        behavior_metrics["eye_contact_frames"] += 0.8
        ret, buffer = cv2.imencode('.jpg', frame)
        yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')

def process_audio_worker():
    global ai_state, semantic_scores
    try:
        ai_state["status"] = "Analyzing response..."
        user_transcript = stop_recording_mic()
        
        if "Error" not in user_transcript:
            # 🚨 FIX: Pass the actual current question to the grader!
            current_q = ai_state["current_question"]
            score = evaluate_semantics(user_transcript, f"A detailed, accurate answer to: {current_q}")
            semantic_scores.append(score)
        
        ai_state["current_q_index"] += 1
        
        if ai_state["current_q_index"] < len(ai_state["questions"]):
            ai_state["current_question"] = ai_state["questions"][ai_state["current_q_index"]]
            ai_state["current_state"] = "QUESTION"
        else:
            ai_state["current_state"] = "COMPLETE"
            calculate_final_cri()
    finally:
        ai_state["is_busy"] = False

def calculate_final_cri():
    global ai_state, semantic_scores, behavior_metrics
    
    avg_s = sum(semantic_scores)/len(semantic_scores) if semantic_scores else 0
    
    # 🚨 FIX: Apply a 1.2x multiplier curve to the harsh semantic score (capped at 100)
    curved_s = min(100.0, avg_s * 1.2) 
    
    total = behavior_metrics["total_frames"]
    eye_ratio = (behavior_metrics["eye_contact_frames"] / total) if total > 0 else 0.8
    avg_b = eye_ratio * 100
    
    # Use the curved semantic score
    cri = (0.6 * curved_s) + (0.4 * avg_b)
    
    ai_state["current_question"] = f"🏁 Final CRI: {cri:.1f}"
    
    # DB Save with Error Handling
    try:
        with app.app_context():
            new_s = InterviewSession(
                firebase_uid=ai_state["active_user_uid"], 
                role=ai_state["target_role"],
                semantic_score=avg_s, 
                behavioral_score=avg_b, 
                overall_cri=cri
            )
            db.session.add(new_s)
            db.session.commit()
            print("✅ Session saved to database successfully!")
    except Exception as e:
        print(f"❌ Database save failed: {e}")

# --- API ROUTES ---

@app.route('/api/upload_resume', methods=['POST'])
@firebase_required
def upload_resume():
    global ai_state, semantic_scores, behavior_metrics
    
    # CRITICAL FIX: Clear arrays to prevent history duplication/data leaking
    semantic_scores.clear()
    behavior_metrics = {"total_frames": 0, "eye_contact_frames": 0}
    ai_state["is_busy"] = False
    
    ai_state["active_user_uid"] = request.user_id
    file = request.files['resume']
    
    # Capture configuration fields
    focus = request.form.get('interviewType', 'Technical')
    difficulty = request.form.get('difficulty', 'Entry Level')
    ai_state["target_role"] = f"Software Engineer ({difficulty} - {focus} Focus)"
    
    # Parse and Generate
    temp = "temp.pdf"
    file.save(temp)
    text = parse_resume(temp)
    ai_state["questions"] = generate_questions(text, ai_state["target_role"])
    
    if os.path.exists(temp):
        os.remove(temp)
    
    ai_state.update({
        "current_q_index": 0, 
        "current_question": ai_state["questions"][0], 
        "current_state": "QUESTION", 
        "status": "Ready."
    })
    
    return jsonify({"success": True})

@app.route('/api/history')
@firebase_required
def get_history():
    sessions = InterviewSession.query.filter_by(firebase_uid=request.user_id).order_by(InterviewSession.date_completed.desc()).all()
    return jsonify([s.to_dict() for s in sessions])

@app.route('/get_status')
def get_status(): 
    return jsonify(ai_state)

@app.route('/next_action', methods=['POST'])
def next_action():
    # Race Condition Fix: Block double-clicks instantly
    if ai_state.get("is_busy"): 
        return jsonify({"success": False, "error": "System busy"})
        
    if ai_state["current_state"] == "QUESTION":
        ai_state["current_state"] = "RECORDING"
        start_recording_mic()
    elif ai_state["current_state"] == "RECORDING":
        ai_state["is_busy"] = True
        ai_state["current_state"] = "ANALYZING" # Locks the frontend UI
        threading.Thread(target=process_audio_worker).start()
        
    return jsonify({"success": True})

@app.route('/video_feed')
def video_feed(): 
    return Response(generate_video_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(debug=True, threaded=True, port=5000)