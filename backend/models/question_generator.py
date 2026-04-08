import os
import re
from mistralai import Mistral
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
api_key = os.getenv("MISTRAL_API_KEY")
client = Mistral(api_key=api_key)

def generate_questions(resume_text, role, num_questions=3):
    is_hr = "HR / Behavioral" in role
    is_experienced = "Experienced" in role
    
    # Extract clean job title (e.g., changes "Software Engineer (Entry Level)" to just "Software Engineer")
    clean_role = role.split('(')[0].strip() if '(' in role else role

    # 1. Determine Focus (Technical vs Behavioral)
    if is_hr:
        focus_instruction = (
            "Generate concise behavioral interview questions using the STAR method format. "
            "CRITICAL: Keep each question strictly under two sentences. Be direct and professional."
        )
    else:
        focus_instruction = (
            "Generate concise, scenario-based technical interview questions relevant to the technologies listed in the resume. "
            "CRITICAL: Keep each question strictly under two sentences. Ask how they would apply a technology to solve a specific problem."
        )

    # 2. Determine Seniority (Entry Level vs Experienced)
    if is_experienced:
        seniority_instruction = (
            "Adopt the persona of a Technical Director interviewing a Senior candidate. Ask about architectural trade-offs, "
            "scalability, system design, and high-stakes problem-solving in production environments."
        )
    else:
        seniority_instruction = (
            "Adopt the persona of a Hiring Manager interviewing an Entry-Level candidate. Focus on core computer science fundamentals, "
            "algorithmic thinking, debugging logic, and specific contributions to their personal/academic projects. "
            "CRITICAL: Do NOT ask trivial definitional questions."
        )

    prompt = f"""
    You are conducting a live interview for the position of {role}.
    
    {focus_instruction}
    {seniority_instruction}
    
    CRITICAL INSTRUCTION: I am already asking the candidate to introduce themselves before this. 
    DO NOT ask any introductory questions like "Tell me about yourself" or "Walk me through your background." 
    Jump STRAIGHT into the core evaluation based on their resume.
    
    Candidate Resume Context:
    {resume_text}

    Generate exactly {num_questions} unique, challenging interview questions based on the candidate's resume. 
    Format the output STRICTLY as a numbered list.
    
    Example Output Format:
    1. [Core scenario question?]
    2. [Core scenario question?]
    3. [Core scenario question?]
    """

    try:
        # Call Mistral API
        chat_response = client.chat.complete(
            model="mistral-tiny",
            messages=[{"role": "user", "content": prompt}]
        )
        content = chat_response.choices[0].message.content
        
        # Parse questions using regex
        questions = re.findall(r'\d\.\s*(.*)', content)
        cleaned_questions = [q.strip().strip('"*') for q in questions if q.strip()]
        
        # Fallback if Mistral fails to return a properly formatted list
        if not cleaned_questions:
            cleaned_questions = [
                "Could you dive deep into the most complex project on your resume?", 
                "What do you consider your strongest technical skill and why?", 
                "How do you handle tight deadlines and shifting priorities?"
            ]

        # --- THE GUARANTEED INTRO QUESTION ---
        intro_question = f"To start things off, could you please introduce yourself and walk me through your background for this {clean_role} position?"
        
        # Combine the intro question with Mistral's specific questions
        final_questions = [intro_question] + cleaned_questions[:num_questions]
        
        return final_questions

    except Exception as e:
        print(f"Mistral Error: {e}")
        # Return a completely safe fallback list of exactly 4 questions if the API crashes
        return [
            f"To start things off, could you please introduce yourself and walk me through your background for this {clean_role} position?",
            "Could you walk me through the most challenging project you've worked on recently?",
            "What is your strongest technical skill, and how did you apply it to solve a real problem?",
            "Can you tell me about a time you had to learn a new technology or domain quickly?"
        ]