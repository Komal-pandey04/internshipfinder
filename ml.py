#ml.py — Internship Matching Logic
# This file finds how much a student's resume matches with available internships.
# It uses Natural Language Processing (NLP) and fuzzy string matching
# to compare resume skills with internship skill requirements.

from __future__ import annotations
import pandas as pd
import re
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from fuzzywuzzy import fuzz   # Used to check how similar two words or phrases are


#Step 1: Load the Internship Dataset

# These columns must exist in the internship CSV file
REQUIRED_COLUMNS = ["title", "company", "location", "description", "skills"]

def load_internships(csv_path: str) -> pd.DataFrame:
    """
    Loads internship data from a CSV file.
    - Checks if all important columns are present.
    - Removes missing or empty values.
    - Returns a clean Pandas DataFrame.
    """
    df = pd.read_csv(csv_path)
    # Make sure all required columns are in the file
    for c in REQUIRED_COLUMNS:
        if c not in df.columns:
            raise ValueError(f"CSV missing required column: {c}")
    # Fill empty cells with blank strings
    df = df.fillna({"location": "", "description": "", "skills": ""})
    # Remove rows without title or company name
    df = df.dropna(subset=["title", "company"]).reset_index(drop=True)
    return df


#Step 2: Clean and Standardize Skills 

# Some skills can be written in many ways. For example:
# "Py" → "Python", "ReactJS" → "React"
# This dictionary helps us keep everything uniform.
_CANON_MAP = {
    "py": "python", "py3": "python", "python3": "python",
    "tf": "tensorflow", "scikit learn": "scikit-learn",
    "sklearn": "scikit-learn",
    "js": "javascript", "node": "node.js",
    "reactjs": "react", "react.js": "react",
    "ts": "typescript",
    "ml": "machine learning",
    "dl": "deep learning",
}

# Words we should ignore if they appear in skills
_STOP_SKILL = {
    "github", "gitlab", "bitbucket", "project", "projects", "blog", "course",
    "accuracy", "machine", "example", "tools", "phone"
}

# This pattern helps us find valid words (like python, html, etc.)
_WORD = re.compile(r"[a-zA-Z0-9+\.\-#]+")

def _to_canonical(s: str) -> Optional[str]:
    """
    Converts skill names to a standard form (canonical).
    Example: "ReactJS" → "react", "py" → "python".
    """
    s = s.strip().lower()
    if not s:
        return None
    # Replace symbols with spaces and clean up text
    s = s.replace("_", " ").replace("/", " ").replace("&", " and ")
    s = re.sub(r"\s+", " ", s)

    # Replace known short forms with full names
    if s in _CANON_MAP:
        s = _CANON_MAP[s]

    # Ignore words that are too short or meaningless
    if len(s) < 2 or s in _STOP_SKILL:
        return None

    return s


def _tokenize_skill_field(s: str) -> List[str]:
    """
    Takes the 'skills' column from CSV and splits it into clean words.
    Example:
      Input  → "Python, ML, TensorFlow"
      Output → ["python", "machine learning", "tensorflow"]
    """
    if not isinstance(s, str):
        return []
    # Split the skills by commas, pipes, or semicolons
    parts = re.split(r"[,\|;/]", s)
    out: List[str] = []
    for p in parts:
        p = p.strip()
        if not p:
            continue
        # Find words that look like valid skills
        words = _WORD.findall(p.lower())
        if not words:
            continue
        cand = " ".join(words)
        can = _to_canonical(cand)
        # Avoid duplicates
        if can and can not in out:
            out.append(can)
    return out


# Step 3: Match Skills (Soft/Fuzzy Matching)

def _best_soft_match(req: str, have: List[str]) -> Tuple[float, Optional[str]]:
    """
    Compares one required skill (from internship) with student's skills.
    Uses fuzzy matching to check similarity (example: 'pyhton' ≈ 'python').
    Returns:
      1.0 = strong match
      0.5 = partial match
      0.0 = no match
    """
    best = 0
    best_str = None
    for h in have:
        r = fuzz.token_set_ratio(req, h)
        if r > best:
            best, best_str = r, h
    if best >= 88:
        return 1.0, best_str   # Excellent match
    if best >= 75:
        return 0.5, best_str   # Partial match
    return 0.0, None           # No match


def _jaccard_bonus(have: List[str], reqs: List[str]) -> float:
    """
    Gives a small bonus score (up to +6%) if the student has more
    skills than required — shows extra knowledge.
    """
    s_have = set(have)
    s_req = set(reqs)
    extra = max(0, len(s_have - s_req))
    return min(0.02 * extra, 0.06)


# Step 4: Define the Output Format

@dataclass
class MatchResult:
    title: str
    company: str
    location: str
    description: str
    skills: str
    match_percent: float


#Step 5: Main Matching Engine 

class Matcher:
    """
    This class takes the internships data and finds
    how much a student's resume matches with each internship.
    """
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        # Pre-tokenize (clean and split) skills of all internships
        self.df["_req_tokens"] = self.df["skills"].apply(_tokenize_skill_field)

    def match(self, resume_text: str, top_k: int = 5, filters: Optional[Dict] = None) -> List[Dict]:
        """
        Main function that compares resume text with internships.
        Returns top K best-matched internships.
        """
        from nlp import extract_skills_from_text  # imported here to prevent circular import issues

        # 1️ Extract student's skills from resume using NLP
        raw_skills = extract_skills_from_text(resume_text, top_k=80)
        have: List[str] = []
        for s in raw_skills:
            can = _to_canonical(s)
            if can and can not in have:
                have.append(can)

        # If no skills were found, continue with empty list
        if not have:
            have = []

        # 2️ Apply filters (like location and domain if selected)
        f_loc = (filters or {}).get("location", "").strip().lower()
        f_dom = (filters or {}).get("domain", "").strip().lower()

        scores: List[Tuple[int, float]] = []

        # 3️ Compare resume with each internship in the dataset
        for i, row in self.df.iterrows():

            # Filter by location
            if f_loc:
                if f_loc not in str(row["location"]).lower():
                    if not (f_loc == "remote" and "remote" in str(row["location"]).lower()):
                        continue

            # Filter by domain (example: data science, web dev)
            if f_dom:
                blob = f"{row['title']} {row['description']}".lower()
                if f_dom not in blob:
                    dom_ok = (
                        (f_dom in {"data science", "ml", "machine learning"} and ("data" in blob or "ml" in blob))
                        or (f_dom in {"web dev", "frontend", "backend"} and ("web" in blob or "frontend" in blob or "backend" in blob))
                        or (f_dom in {"mobile"} and ("android" in blob or "ios" in blob or "flutter" in blob))
                    )
                    if not dom_ok:
                        continue

            reqs = row["_req_tokens"]
            if not reqs:
                # If internship has no skills listed → skip
                scores.append((i, 0.0))
                continue

            # 4️ Compare each required skill with student's skills
            weight_sum = 0.0
            for req in reqs:
                w, _ = _best_soft_match(req, have)
                weight_sum += w

            # 5️ Calculate percentage score
            coverage = weight_sum / max(1, len(reqs))
            bonus = _jaccard_bonus(have, reqs)
            score = max(0.0, min(1.0, coverage + bonus))  # final score between 0 and 1
            scores.append((i, score))

        # 6️ Sort by match percentage (highest first)
        scores.sort(key=lambda x: x[1], reverse=True)

        # 7️ Prepare final list of top internships
        results: List[Dict] = []
        for i, sc in scores[: max(1, top_k)]:
            row = self.df.iloc[i]
            results.append({
                "title": row["title"],
                "company": row["company"],
                "location": row["location"],
                "description": row["description"],
                "skills": row["skills"],

                # ⭐ NEW: Return apply_link to your Streamlit app
                "apply_link": row.get("apply_link", "#"),

                "match_percent": round(sc * 100, 1)
            })
        return results
