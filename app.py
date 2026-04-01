from flask import Flask, render_template, Response, jsonify
import cv2
import threading
import time
import sys
import os

# Ensure local imports for Mistral and SpeechEngine work
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

app = Flask(__name__)

# --- GLOBAL STATE ---
ai_state = {
    "status": "Ready.",
    "current_state": "IDLE", 
    "current_question": "Click 'Start Interview' to begin.",
    "questions": [],
    "current_q_index": 0,
    "is_busy": False
}

semantic_scores = []
behavior_metrics = {"total_frames": 0, "eye_contact_frames": 0, "anxiety_frames": 0}

# Initialize Camera globally
camera = cv2.VideoCapture(0)

# --- VIDEO GENERATOR ---

def generate_video_frames():
    """Captures frames, updates behavior metrics, and streams to UI."""
    global behavior_metrics
    while True:
        success, frame = camera.read()
        if not success:
            break
        else:
            # Simple behavior metric tracking (Example: count total frames)
            behavior_metrics["total_frames"] += 1
            
            # (Optional: Add your face/eye detection logic here)

            # Encode and yield the frame
            ret, buffer = cv2.imencode('.jpg', frame)
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

# --- BACKGROUND WORKERS ---

def background_mistral_worker():
    """Phase 1: Reading Resume & Generating Questions"""
    global ai_state
    try:
        ai_state["is_busy"] = True
        ai_state["current_state"] = "READING"
        ai_state["status"] = "Reading Resume & Building AI Context..."
        
        # Mocking logic - Replace with your actual imports
        # from backend.models.resume_parser import parse_resume
        # from backend.models.question_generator import generate_questions
        
        time.sleep(2) # Simulating processing
        questions = ["Tell me about your experience with Python.", "How do you handle tight deadlines?", "Explain a technical challenge you solved."]
        
        if questions:
            ai_state["questions"] = questions
            ai_state["current_q_index"] = 0
            ai_state["current_question"] = questions[0]
            ai_state["current_state"] = "QUESTION"
            ai_state["status"] = "Question 1 Loaded. Ready for recording."
        else:
            ai_state["status"] = "Error: Questions not found."
    except Exception as e:
        ai_state["status"] = f"Error: {e}"
    finally:
        ai_state["is_busy"] = False

def background_answer_worker():
    """Phase 2: Recording, Transcription, and Semantic Analysis"""
    global ai_state, semantic_scores
    try:
        ai_state["is_busy"] = True
        ai_state["current_state"] = "RECORDING"
        ai_state["status"] = "🎤 Recording... Speak now!"
        
        # Replace with your: transcribe_audio_from_mic()
        time.sleep(3) 
        user_transcript = "Sample user response" 
        
        if user_transcript:
            ai_state["status"] = "🧠 Processing Answer Quality..."
            # Replace with your: evaluate_semantics()
            score = 85.0 
            semantic_scores.append(score)
            
            ai_state["current_q_index"] += 1
            if ai_state["current_q_index"] < len(ai_state["questions"]):
                ai_state["current_question"] = ai_state["questions"][ai_state["current_q_index"]]
                ai_state["current_state"] = "QUESTION"
                ai_state["status"] = f"Question {ai_state['current_q_index']+1} Ready."
            else:
                ai_state["current_state"] = "COMPLETE"
                calculate_final_cri()
        else:
            ai_state["status"] = "⚠️ No audio detected. Try again."
            ai_state["current_state"] = "QUESTION"
    except Exception as e:
        ai_state["status"] = f"Error: {e}"
    finally:
        ai_state["is_busy"] = False

def calculate_final_cri():
    """Phase 3: Calculating Candidate Readiness Index (CRI)"""
    global ai_state, semantic_scores, behavior_metrics
    avg_semantic = sum(semantic_scores) / len(semantic_scores) if semantic_scores else 0
    frames = behavior_metrics["total_frames"]
    
    # Example logic for eye contact
    eye_ratio = (behavior_metrics["eye_contact_frames"] / frames) if frames > 0 else 0.5
    
    cri_score = (0.6 * avg_semantic) + (0.4 * (eye_ratio * 100))
    ai_state["current_question"] = f"🏆 FINAL CRI: {round(cri_score, 1)}/100"
    ai_state["status"] = "🏁 Interview Complete!"

# --- ROUTES ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_status')
def get_status():
    return jsonify(ai_state)

@app.route('/next_action', methods=['POST'])
def next_action():
    if ai_state["is_busy"]:
        return jsonify({"success": False, "message": "System is busy"})

    if ai_state["current_state"] == "IDLE":
        threading.Thread(target=background_mistral_worker).start()
    elif ai_state["current_state"] == "QUESTION":
        threading.Thread(target=background_answer_worker).start()
    
    return jsonify({"success": True})

@app.route('/video_feed')
def video_feed():
    return Response(generate_video_frames(), 
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    # threaded=True is vital for handling the video stream and API calls simultaneously
    app.run(debug=True, threaded=True, port=5000)