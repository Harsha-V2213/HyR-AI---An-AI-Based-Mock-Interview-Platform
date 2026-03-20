import sys
import os
import time
import threading
import cv2
from deepface import DeepFace

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# --- GLOBAL SHARED MEMORY ---
is_interview_active = True
semantic_scores = []
behavior_metrics = {
    "total_frames": 0,
    "eye_contact_frames": 0,
    "anxiety_frames": 0
}
audio_brain_status = "Initializing..."

# --- NEW ASYNC VARIABLES ---
current_emotion = "Warming up..."
frame_for_analysis = None  # Holds the frame for the background worker

def emotion_worker_thread():
    """
    Runs completely in the background. It grabs a frame, analyzes emotion, 
    and updates the UI without EVER freezing the camera loop.
    """
    global is_interview_active, frame_for_analysis, current_emotion, behavior_metrics
    
    while is_interview_active:
        if frame_for_analysis is not None:
            try:
                # Analyze the frame silently
                analysis = DeepFace.analyze(frame_for_analysis, actions=['emotion'], enforce_detection=False)
                current_emotion = analysis[0]['dominant_emotion']
                
                # Log anxiety for the final score
                if current_emotion in ['fear', 'sad', 'angry']:
                    behavior_metrics["anxiety_frames"] += 1
            except Exception:
                pass
            
            # Clear the frame so we wait for the next one
            frame_for_analysis = None
            
        # Sleep for a fraction of a second to prevent CPU overload
        time.sleep(0.5)

def audio_interview_pipeline(pdf_path, job_role, num_questions):
    global is_interview_active, semantic_scores, audio_brain_status
    
    audio_brain_status = "Warming up SentenceBERT..."
    from models.resume_parser import parse_resume
    from models.question_generator import generate_questions
    from models.speech_analyzer import transcribe_audio_from_mic, evaluate_semantics
    
    audio_brain_status = "Reading Resume..."
    parsed_data = parse_resume(pdf_path)
    if "error" in parsed_data:
        print(f"Error: {parsed_data['error']}")
        is_interview_active = False
        return

    audio_brain_status = "Mistral generating questions..."
    questions = generate_questions(parsed_data, job_role, num_questions)
    
    if questions and "Error" in questions[0]:
        print(questions[0])
        is_interview_active = False
        return

    time.sleep(1)

    for i, question_text in enumerate(questions, 1):
        audio_brain_status = f"Question {i}: Listening..."
        print("\n" + "-"*50)
        print(f"🗣️ QUESTION {i} OF {len(questions)}:")
        print(f"{question_text}")
        print("-"*50)
        
        user_transcript = transcribe_audio_from_mic()
        
        if "Error:" not in user_transcript:
            audio_brain_status = "Evaluating Answer..."
            score = evaluate_semantics(user_transcript, question_text)
            semantic_scores.append(score)
            print(f"\n📊 Semantic Score: {score}% | Transcript: {user_transcript[:60]}...")
        else:
            print(f"\n⚠️ Audio Error: {user_transcript}")
            semantic_scores.append(0.0)
            
        if i < len(questions):
            audio_brain_status = "Waiting for you to proceed..."
            print("\n" + "."*50)
            input("⏯️  Press [ENTER] in this terminal when you are ready for the next question...")
            print("."*50)
            
    is_interview_active = False

def run_unified_platform(pdf_path):
    global is_interview_active, behavior_metrics, audio_brain_status, frame_for_analysis, current_emotion

    # 1. Start Audio Thread
    audio_thread = threading.Thread(target=audio_interview_pipeline, args=(pdf_path, "Data Scientist", 3))
    audio_thread.start()

    # 2. Start Emotion Worker Thread (THE FIX)
    emotion_thread = threading.Thread(target=emotion_worker_thread)
    emotion_thread.start()

    # 3. Main Video Loop
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW) 
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    
    while cap.isOpened() and is_interview_active:
        success, image = cap.read()
        if not success:
            continue

        image = cv2.flip(image, 1)
        gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        behavior_metrics["total_frames"] += 1

        # Fast Eye Contact Tracking (Will no longer stutter!)
        faces = face_cascade.detectMultiScale(gray_image, scaleFactor=1.1, minNeighbors=4, minSize=(40, 40))
        if len(faces) > 0:
            behavior_metrics["eye_contact_frames"] += 1
            for (x, y, w, h) in faces:
                cv2.rectangle(image, (x, y), (x+w, y+h), (0, 255, 0), 2)
                cv2.putText(image, "Eye Contact: Good", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        else:
            cv2.putText(image, "Face Lost! Look here.", (20, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        # Hand off a frame to the background Emotion Thread once per second
        if behavior_metrics["total_frames"] % 30 == 0:
            frame_for_analysis = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # Draw UI
        cv2.putText(image, f"AI Status: {audio_brain_status}", (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        
        emotion_color = (0, 0, 255) if current_emotion in ['fear', 'sad', 'angry'] else (255, 255, 255)
        cv2.putText(image, f"Emotion: {current_emotion.capitalize()}", (20, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, emotion_color, 2)

        cv2.imshow('AI Mock Interview', image)

        if cv2.waitKey(30) & 0xFF == ord('q'):
            is_interview_active = False
            break

    cap.release()
    cv2.destroyAllWindows()
    audio_thread.join()
    emotion_thread.join()

    # --- SCORE CALCULATION ---
    print("\n" + "="*50)
    print("🏁 INTERVIEW COMPLETE! CALCULATING RESULTS...")
    print("="*50)
    
    avg_semantic = sum(semantic_scores) / len(semantic_scores) if semantic_scores else 0.0
    frames = behavior_metrics["total_frames"]
    eye_contact_ratio = behavior_metrics["eye_contact_frames"] / frames if frames > 0 else 0
    anxiety_ratio = behavior_metrics["anxiety_frames"] / (frames / 30) if frames > 0 else 0
    
    calm_ratio = max(0, 1.0 - anxiety_ratio)
    behavior_score = ((eye_contact_ratio * 0.5) + (calm_ratio * 0.5)) * 100
    cri = (0.6 * avg_semantic) + (0.4 * behavior_score)
    
    print(f"🧠 Technical Semantic Score (S): {round(avg_semantic, 1)} / 100")
    print(f"👀 Behavioral Confidence Score (B): {round(behavior_score, 1)} / 100")
    print(f"🏆 FINAL CANDIDATE READINESS INDEX (CRI): {round(cri, 1)} / 100")

if __name__ == "__main__":
    target_pdf = "sample_resume.pdf" 
    if os.path.exists(target_pdf):
        run_unified_platform(target_pdf)
    else:
        print(f"Error: Could not find '{target_pdf}'")