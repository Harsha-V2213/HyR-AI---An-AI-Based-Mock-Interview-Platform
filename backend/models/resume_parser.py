import fitz  # PyMuPDF
import spacy
import re

# Load the English NLP model
nlp = spacy.load("en_core_web_sm")

def extract_text_from_pdf(pdf_path):
    """Extracts raw text from a given PDF file using PyMuPDF."""
    text = ""
    try:
        # Open the PDF document
        doc = fitz.open(pdf_path)
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text += page.get_text("text") + "\n"
        doc.close()
    except Exception as e:
        print(f"Error reading PDF: {e}")
    
    # Basic cleanup: remove extra white spaces and newlines
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def parse_resume(pdf_path):
    """
    Parses the resume to extract text and identify key entities.
    Returns a dictionary of the parsed data.
    """
    raw_text = extract_text_from_pdf(pdf_path)
    
    if not raw_text:
        return {"error": "Could not extract text from the provided file."}

    # Process the text with spaCy NLP model
    doc = nlp(raw_text)
    
    # Initialize dictionaries to hold categorized entities
    parsed_data = {
        "organizations": set(),
        "locations": set(),
        "technologies_and_terms": set(), # Using NOUN and PROPN as proxies for skills
        "raw_text": raw_text
    }

    # Extract Named Entities
    for ent in doc.ents:
        if ent.label_ == "ORG":
            parsed_data["organizations"].add(ent.text)
        elif ent.label_ == "GPE": # Geopolitical entity (cities, countries)
            parsed_data["locations"].add(ent.text)

    # Convert sets back to lists for easy JSON serialization later
    parsed_data["organizations"] = list(parsed_data["organizations"])
    parsed_data["locations"] = list(parsed_data["locations"])
    
    # A simple heuristic to grab potential tech skills (Proper Nouns)
    for token in doc:
        if token.pos_ == "PROPN" and len(token.text) > 2:
            parsed_data["technologies_and_terms"].add(token.text)
            
    parsed_data["technologies_and_terms"] = list(parsed_data["technologies_and_terms"])[:20] # Limit to top 20

    return parsed_data

# --- Testing the Module Locally ---
if __name__ == "__main__":
    # To test this, place a sample PDF resume in your project folder
    sample_pdf = "sample_resume.pdf" # Replace with your actual PDF file name
    
    import os
    if os.path.exists(sample_pdf):
        print(f"Parsing {sample_pdf}...\n")
        result = parse_resume(sample_pdf)
        
        print("--- EXTRACTED ORGANIZATIONS ---")
        print(result["organizations"])
        
        print("\n--- POTENTIAL SKILLS / TERMS ---")
        print(result["technologies_and_terms"])
    else:
        print(f"Please put a file named '{sample_pdf}' in the same folder to test.")