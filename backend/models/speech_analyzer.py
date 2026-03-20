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

def transcribe_audio_from_mic():
    """
    Records audio in the background until the user presses Enter, 
    then converts that speech to text.
    """
    filename = "temp_answer.wav"
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000
    
    p = pyaudio.PyAudio()
    
    try:
        stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, 
                        input=True, frames_per_buffer=CHUNK)
    except Exception as e:
        return f"Error accessing microphone: {e}"
    
    frames = []
    is_recording = True
    
    # This function will run in the background
    def capture_audio():
        while is_recording:
            try:
                data = stream.read(CHUNK, exception_on_overflow=False)
                frames.append(data)
            except Exception:
                pass
                
    print("\n🟢 Recording! Speak your answer clearly.")
    
    # 1. Start recording in a background thread
    record_thread = threading.Thread(target=capture_audio)
    record_thread.start()
    
    # 2. Wait for the user to press Enter
    input("   (Press [ENTER] when you are finished speaking...)")
    
    # 3. Stop recording
    is_recording = False
    record_thread.join()
    
    stream.stop_stream()
    stream.close()
    p.terminate()
    
    # 4. Save the recorded frames to a temporary WAV file
    wf = wave.open(filename, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()
    
    # 5. Transcribe the saved file
    recognizer = sr.Recognizer()
    print("Processing audio...")
    
    # Read the audio into memory FIRST, so the file naturally closes
    with sr.AudioFile(filename) as source:
        audio_data = recognizer.record(source)
        
    # NOW we can safely evaluate it and delete the file without Windows getting mad
    try:
        transcript = recognizer.recognize_google(audio_data)
        if os.path.exists(filename): 
            os.remove(filename) 
        return transcript
        
    except sr.UnknownValueError:
        if os.path.exists(filename): 
            os.remove(filename)
        return "Error: Could not understand the audio. (Did you speak?)"
        
    except sr.RequestError as e:
        if os.path.exists(filename): 
            os.remove(filename)
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