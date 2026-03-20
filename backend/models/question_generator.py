import os
from mistralai import Mistral
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("MISTRAL_API_KEY")

def generate_questions(parsed_resume_data, job_role="Software Engineer", num_questions=1):
    """
    Asks Mistral-7B to generate tailored interview questions ONLY.
    Returns a simple list of strings: ['Question 1?', 'Question 2?']
    """
    if not api_key:
        return ["Error: MISTRAL_API_KEY not found in .env file."]

    client = Mistral(api_key=api_key)
    skills = ", ".join(parsed_resume_data.get("technologies_and_terms", []))
    organizations = ", ".join(parsed_resume_data.get("organizations", []))
    
    prompt = f"""
    You are an expert technical interviewer hiring for a {job_role} position.
    Review the following candidate profile extracted from their resume:
    - Key Skills/Terms: {skills}
    - Past Organizations: {organizations}
    
    Generate exactly {num_questions} professional interview questions for this candidate. 
    Make 1 question about their past experience and the rest testing their technical skills.
    Do not include any introductory or concluding text, just return the numbered list of questions.
    """

    try:
        chat_response = client.chat.complete(
            model="mistral-small-latest",
            messages=[{"role": "user", "content": prompt}]
        )
        
        raw_output = chat_response.choices[0].message.content
        questions = [q.strip() for q in raw_output.split('\n') if q.strip()]
        return questions
        
    except Exception as e:
        return [f"Error communicating with Mistral API: {e}"]