import speech_recognition as sr
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import os

# Load the SentenceBERT model
print("Loading SentenceBERT model...")
sbert_model = SentenceTransformer('all-MiniLM-L6-v2')

def transcribe_audio(audio_file_path):
    """
    Receives an audio file saved by the Flask API, 
    transcribes it using Google Speech Recognition, and returns the text.
    """
    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(audio_file_path) as source:
            audio_data = recognizer.record(source)
            
        transcript = recognizer.recognize_google(audio_data)
        return transcript
        
    except sr.UnknownValueError:
        return "Error: Could not understand the audio. (Did you speak?)"
        
    except sr.RequestError as e:
        return f"Error: Could not request results; {e}"
    except Exception as e:
        return f"Error processing audio: {e}"

def evaluate_semantics(candidate_answer, expected_answer):
    """
    Compares the candidate's transcribed answer to the expected answer 
    using SentenceBERT and Cosine Similarity.
    """
    if "Error:" in candidate_answer:
        return 0.0

    embeddings = sbert_model.encode([candidate_answer, expected_answer])
    similarity_score = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
    
    return round(float(similarity_score * 100), 2)