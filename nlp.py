# nlp.py  (Skill Extraction and Resume Parsing)

# Importing required libraries
import spacy                      # For natural language processing (text analysis)
from fuzzywuzzy import process    # For fuzzy (approximate) text matching
import json                       # For working with JSON data
from typing import List, Dict     # For type hinting (helps show data types)
import re                         # For regular expressions (pattern searching)

# Load small English NLP model from SpaCy
nlp = spacy.load("en_core_web_sm")

# A list of common technical skills (you can add more)
CANONICAL_SKILLS = [
    "python", "java", "c++", "sql", "mysql", "pandas", "numpy", "scikit-learn", "tensorflow",
    "pytorch", "nlp", "machine learning", "deep learning", "data analysis", "visualization",
    "react", "node.js", "javascript", "html", "css", "aws", "azure", "git", "docker", "kubernetes"
]

# Function: extract_skills_from_text
# Description: Finds and returns skills mentioned in the given text
def extract_skills_from_text(text: str, top_k=40) -> List[str]:
    """Extract skills from text using rule-based and fuzzy matching."""

    # Convert text to lowercase to make matching easier
    text_lower = text.lower()
    found = set()  # A set to store found skills (automatically removes duplicates)

    # Process text using SpaCy NLP
    doc = nlp(text)

    # Extract named entities (like organizations, products, or languages)
    for ent in doc.ents:
        if ent.label_ in ("ORG", "PRODUCT", "SKILL", "WORK_OF_ART", "NORP", "LANGUAGE"):
            found.add(ent.text.lower())

    # Extract short noun phrases (e.g., "data analysis", "deep learning")
    for chunk in doc.noun_chunks:
        if len(chunk.text) < 40:
            found.add(chunk.text.lower().strip())

    # Check if any skill from the list appears directly in the text
    for skill in CANONICAL_SKILLS:
        if skill in text_lower:
            found.add(skill)

    # Prepare a clean version of text tokens (remove stop words and punctuation)
    tokens = [t.text for t in doc if not t.is_stop and not t.is_punct]
    joined = " ".join(tokens)

    # Use fuzzy matching to find similar skill names (e.g., "pythin" → "python")
    for skill in CANONICAL_SKILLS:
        score = process.extractOne(skill, [joined])[1]  # get similarity score
        if score > 85:  # if similarity score is above 85%, consider it a match
            found.add(skill)

    # Clean up skill names (remove unwanted symbols and extra spaces)
    cleaned = []
    for x in found:
        x = re.sub(r'[^a-z0-9+.# -]', '', x)  # keep only valid characters
        x = x.strip()
        if len(x) > 1 and len(x) < 40:
            cleaned.append(x)

    # Remove duplicates while keeping order
    cleaned = list(dict.fromkeys(cleaned))

    # Return the top 'k' skills
    return cleaned[:top_k]


# Function: parse_resume_text_for_meta
# Description: Extracts name, email, phone, and skills from resume text
def parse_resume_text_for_meta(text: str) -> Dict:
    """Extract basic information like name, emails, phones, and skills from resume text."""

    # Find all email addresses in text
    emails = re.findall(r'[\w\.-]+@[\w\.-]+', text)

    # Find all phone numbers (supports +91, dashes, spaces, etc.)
    phones = re.findall(r'\+?\d[\d\-\s]{7,}\d', text)

    # Look for name near the top of the resume
    top_text = text[:400]  # Only check first 400 characters (names are usually at the top)
    name = None
    lines = [l.strip() for l in top_text.splitlines() if l.strip()]  # split into non-empty lines

    if lines:
        candidate = lines[0]  # take the first line as possible name
        words = candidate.split()
        # Check if line looks like a name (short and has capitalized words)
        if len(words) <= 4 and sum(1 for w in words if w[:1].isupper()) >= 1:
            name = candidate

    # Extract skills using our previous function
    skills = extract_skills_from_text(text)

    # Return all extracted information as a dictionary
    return {
        "name": name,
        "emails": list(set(emails)),   # remove duplicate emails
        "phones": list(set(phones)),   # remove duplicate phone numbers
        "skills": skills               # list of extracted skills
    }
