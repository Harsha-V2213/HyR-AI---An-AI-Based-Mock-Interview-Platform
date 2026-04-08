from flask import Flask, Response, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, auth
from functools import wraps
import threading
import sys
import os
from datetime import datetime
import traceback

load_dotenv()
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from backend.models.resume_parser import parse_resume
from backend.models.question_generator import generate_questions
from backend.models.speech_analyzer import start_recording_mic, stop_recording_mic, evaluate_semantics
# 🚨 IMPORTING THE WEB-ADAPTED PROCTOR 🚨
from backend.models.interview_proctor import generate_video_frames, behavior_metrics, reset_behavior_metrics

app = Flask(__name__)
CORS(app) 

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

try:
    cred = credentials.Certificate("firebase-key.json")
    firebase_admin.initialize_app(cred)
    print("✅ Firebase Admin Active")
except Exception as e:
    print(f"⚠️ Firebase Error: {e}")

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
            "semantic_score": round(self.semantic_score, 1),
            "behavioral_score": round(self.behavioral_score, 1),
            "overall_cri": round(self.overall_cri, 1),
            "date": self.date_completed.isoformat()
        }

with app.app_context():
    db.create_all()

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

ai_state = {
    "status": "Ready.", 
    "current_state": "IDLE", 
    "current_question": "Waiting...",
    "questions": [], 
    "current_q_index": 0, 
    "is_busy": False, 
    "target_role": "", 
    "active_user_uid": None,
    "results": None 
}

semantic_scores = []

def process_audio_worker():
    global ai_state, semantic_scores
    try:
        ai_state["status"] = "Analyzing response..."
        user_transcript = stop_recording_mic()
        
        if "Error" not in user_transcript:
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
    global ai_state, semantic_scores
    
    avg_s = sum(semantic_scores)/len(semantic_scores) if semantic_scores else 0
    curved_s = min(100.0, avg_s * 1.2) 
    
    total = behavior_metrics["total_frames"]
    eye_ratio = (behavior_metrics["eye_contact_frames"] / total) if total > 0 else 0.8
    avg_b = eye_ratio * 100
    
    cri = (0.6 * curved_s) + (0.4 * avg_b)
    
    ai_state["current_question"] = "Session Complete. Formulating analytics..."
    ai_state["results"] = {
        "semantic": round(float(curved_s), 1),
        "behavioral": round(float(avg_b), 1),
        "cri": round(float(cri), 1)
    }
    
    try:
        with app.app_context():
            if not ai_state.get("active_user_uid"): raise ValueError("Active User UID is missing!")
            new_s = InterviewSession(
                firebase_uid=ai_state["active_user_uid"], 
                role=ai_state["target_role"],
                semantic_score=float(curved_s), 
                behavioral_score=float(avg_b), 
                overall_cri=float(cri)
            )
            db.session.add(new_s)
            db.session.commit()
            print("✅ Session saved to database successfully!")
    except Exception as e:
        print("❌ DATABASE SAVE FAILED ❌")
        traceback.print_exc()

@app.route('/api/upload_resume', methods=['POST'])
@firebase_required
def upload_resume():
    global ai_state, semantic_scores
    semantic_scores.clear()
    reset_behavior_metrics()
    
    ai_state["is_busy"] = False
    ai_state["results"] = None
    ai_state["active_user_uid"] = request.user_id
    
    file = request.files['resume']
    focus = request.form.get('interviewType', 'Technical')
    difficulty = request.form.get('difficulty', 'Entry Level')
    ai_state["target_role"] = f"Software Engineer ({difficulty} - {focus} Focus)"
    
    temp = "temp.pdf"
    file.save(temp)
    text = parse_resume(temp)
    ai_state["questions"] = generate_questions(text, ai_state["target_role"])
    
    if os.path.exists(temp): os.remove(temp)
    
    ai_state.update({"current_q_index": 0, "current_question": ai_state["questions"][0], "current_state": "QUESTION", "status": "Ready."})
    return jsonify({"success": True})

@app.route('/api/history')
@firebase_required
def get_history():
    sessions = InterviewSession.query.filter_by(firebase_uid=request.user_id).order_by(InterviewSession.date_completed.desc()).all()
    return jsonify([s.to_dict() for s in sessions])

@app.route('/get_status')
def get_status(): return jsonify(ai_state)

@app.route('/next_action', methods=['POST'])
def next_action():
    if ai_state.get("is_busy"): return jsonify({"success": False})
    if ai_state["current_state"] == "QUESTION":
        ai_state["current_state"] = "RECORDING"
        start_recording_mic()
    elif ai_state["current_state"] == "RECORDING":
        ai_state["is_busy"] = True
        ai_state["current_state"] = "ANALYZING"
        threading.Thread(target=process_audio_worker).start()
    return jsonify({"success": True})

@app.route('/video_feed')
def video_feed(): 
    return Response(generate_video_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(debug=True, threaded=True, port=5000)