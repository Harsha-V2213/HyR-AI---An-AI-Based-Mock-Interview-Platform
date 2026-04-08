import speech_recognition as sr
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import pyaudio
import wave
import threading
import os

# Load the SentenceBERT model
print("Loading SentenceBERT model...")
sbert_model = SentenceTransformer('all-MiniLM-L6-v2')

# --- GLOBAL VARIABLES FOR API-CONTROLLED RECORDING ---
_is_recording = False
_frames = []
_p = None
_stream = None
_record_thread = None
_filename = "temp_answer.wav"

def start_recording_mic():
    """Starts recording audio from the local microphone in the background."""
    global _is_recording, _frames, _p, _stream, _record_thread
    
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000
    
    _p = pyaudio.PyAudio()
    try:
        _stream = _p.open(format=FORMAT, channels=CHANNELS, rate=RATE, 
                        input=True, frames_per_buffer=CHUNK)
    except Exception as e:
        print(f"Error accessing microphone: {e}")
        return
        
    _frames = []
    _is_recording = True
    
    def capture_audio():
        while _is_recording:
            try:
                data = _stream.read(CHUNK, exception_on_overflow=False)
                _frames.append(data)
            except Exception:
                pass
                
    print("\n🟢 Recording started via Web UI.")
    _record_thread = threading.Thread(target=capture_audio)
    _record_thread.start()

def stop_recording_mic():
    """Stops the recording, saves to WAV, and transcribes it."""
    global _is_recording, _frames, _p, _stream, _record_thread, _filename
    
    if not _is_recording:
        return "Error: Was not recording."
        
    _is_recording = False
    if _record_thread:
        _record_thread.join()
        
    if _stream:
        _stream.stop_stream()
        _stream.close()
    if _p:
        _p.terminate()
        
    print("\n🔴 Recording stopped. Processing audio...")
    
    # Save the recorded frames to a temporary WAV file
    wf = wave.open(_filename, 'wb')
    wf.setnchannels(1)
    wf.setsampwidth(_p.get_sample_size(pyaudio.paInt16))
    wf.setframerate(16000)
    wf.writeframes(b''.join(_frames))
    wf.close()
    
    # Transcribe the saved file
    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(_filename) as source:
            audio_data = recognizer.record(source)
            
        transcript = recognizer.recognize_google(audio_data)
        if os.path.exists(_filename): 
            os.remove(_filename) 
        return transcript
        
    except sr.UnknownValueError:
        if os.path.exists(_filename): 
            os.remove(_filename)
        return "Error: Could not understand the audio. (Did you speak?)"
        
    except sr.RequestError as e:
        if os.path.exists(_filename): 
            os.remove(_filename)
        return f"Error: Could not request results; {e}"

def evaluate_semantics(candidate_answer, expected_answer):
    """
    Compares the candidate's transcribed answer to the expected answer 
    using SentenceBERT and Cosine Similarity.
    """
    if "Error:" in candidate_answer:
        return 0.0

    embeddings = sbert_model.encode([candidate_answer, expected_answer])
    similarity_score = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
    
    return round(similarity_score * 100, 2)