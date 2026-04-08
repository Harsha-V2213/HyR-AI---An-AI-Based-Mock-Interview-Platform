import os
import re
from mistralai import Mistral
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
api_key = os.getenv("MISTRAL_API_KEY")
client = Mistral(api_key=api_key)

def generate_questions(resume_text, role, num_questions=5):
    is_hr = "HR / Behavioral" in role
    is_experienced = "Experienced" in role
    
    # Extract clean job title
    clean_role = role.split('(')[0].strip() if '(' in role else role

    # 1. Determine Focus
    if is_hr:
        focus_instruction = (
            "Generate concise behavioral interview questions using the STAR method format. "
            "CRITICAL: Keep each question strictly under two sentences. Be direct and professional."
        )
    else:
        focus_instruction = (
            "Generate concise, scenario-based technical interview questions relevant to the technologies listed in the resume. "
            "CRITICAL: Keep each question strictly under two sentences."
        )

    # 2. Determine Seniority & Strict Ordering
    if is_experienced:
        seniority_instruction = (
            "Adopt the persona of a Technical Director interviewing a Senior candidate. Ask about architectural trade-offs, "
            "scalability, system design, and high-stakes problem-solving in production environments."
        )
    else:
        seniority_instruction = (
            "Adopt the persona of a friendly engineering manager interviewing an intern or recent graduate. "
            "YOU MUST STRICTLY OBEY THESE RULES: "
            "1. NO SYSTEM DESIGN OR ADVANCED DSA: Never ask about microservices, scalability, dynamic programming, or complex graphs. "
            "2. THE QUESTION MENU: You must generate exactly 5 questions in this EXACT order: "
            "   - Question 1 (Resume Skill): Ask about a specific general technical skill or achievement listed on their resume. "
            "   - Question 2 (CS Fundamental): Ask about core CS fundamentals (e.g., OOP principles, basic SQL, HTTP requests). "
            "   - Question 3 (Basic DSA): Ask a basic programming logic concept (e.g., arrays, loops, strings). "
            "   - Question 4 (Situational): Ask how they would handle a basic workplace scenario (e.g., debugging a tough error, working with a team). "
            "   - Question 5 (Project Deep Dive): Ask them to describe the overarching goal or a basic challenge of a specific project on their resume. "
            "3. KEEP IT SHORT: Ask exactly ONE simple, single-part question at a time."
        )

    prompt = f"""
    You are conducting a live interview for the position of {role}.
    
    {focus_instruction}
    {seniority_instruction}
    
    CRITICAL INSTRUCTION: I am already asking the candidate to introduce themselves before this. 
    DO NOT ask any introductory questions like "Tell me about yourself" or "Walk me through your background." 
    Jump STRAIGHT into Question 1 of the menu based on their resume.
    
    Candidate Resume Context:
    {resume_text}

    Generate exactly {num_questions} unique, balanced interview questions following the exact order of the Question Menu above. 
    Format the output STRICTLY as a numbered list.
    
    Example Output Format:
    1. [Question about a Resume Skill]
    2. [Question about a CS Fundamental]
    3. [Question about Basic DSA]
    4. [Question about a Situational Scenario]
    5. [Question about a Project Description]
    """

    try:
        # Call Mistral API
        chat_response = client.chat.complete(
            model="mistral-small-latest", 
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2 # Forces strict adherence to the requested order
        )
        content = chat_response.choices[0].message.content
        
        # Parse questions using regex
        questions = re.findall(r'\d\.\s*(.*)', content)
        cleaned_questions = [q.strip().strip('"*') for q in questions if q.strip()]
        
        # Fallback if Mistral fails
        if len(cleaned_questions) < num_questions:
            cleaned_questions = [
                "Looking at your resume, what do you consider your strongest technical skill and why?", 
                "Can you explain the basic principles of Object-Oriented Programming?", 
                "How would you approach finding a specific value in a large array or list?",
                "Tell me about a time you ran into a difficult bug. How did you debug it?",
                "Could you briefly describe the goal of the main project listed on your resume?"
            ]

        # --- THE GUARANTEED INTRO QUESTION ---
        intro_question = f"To start things off, could you please introduce yourself and walk me through your background for this {clean_role} position?"
        
        # Combine the intro question with Mistral's perfectly ordered menu
        final_questions = [intro_question] + cleaned_questions[:num_questions]
        
        return final_questions

    except Exception as e:
        print(f"Mistral Error: {e}")
        return [
            f"To start things off, could you please introduce yourself and walk me through your background for this {clean_role} position?",
            "Looking at your resume, what do you consider your strongest technical skill and why?", 
            "Can you explain the basic principles of Object-Oriented Programming?", 
            "How would you approach finding a specific value in a large array or list?",
            "Tell me about a time you ran into a difficult bug. How did you debug it?",
            "Could you briefly describe the goal of the main project listed on your resume?"
        ]