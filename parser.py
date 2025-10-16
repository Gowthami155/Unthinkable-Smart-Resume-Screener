# app/parser.py
import re
import pdfplumber
from typing import Dict, List
import nltk
import os

# ensure punkt available
try:
    nltk.data.find("tokenizers/punkt")
except Exception:
    nltk.download("punkt")

from nltk.tokenize import sent_tokenize

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

def extract_text_from_pdf(path: str) -> str:
    """Extract full text from PDF using pdfplumber."""
    text_parts = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            txt = page.extract_text() or ""
            text_parts.append(txt)
    return "\n".join(text_parts).strip()

def load_skills(skill_file: str = None) -> List[str]:
    if not skill_file:
        skill_file = os.path.join(BASE_DIR, "skills.txt")
    skills = []
    try:
        with open(skill_file, "r", encoding="utf-8") as f:
            for line in f:
                s = line.strip()
                if s:
                    skills.append(s.lower())
    except FileNotFoundError:
        # fallback short list
        skills = ["python", "java", "sql", "aws", "docker", "react"]
    return skills

def extract_skills(text: str, skills_list: List[str]) -> List[str]:
    """Simple matching of skills list inside text (case-insensitive)."""
    found = set()
    t = text.lower()
    for skill in skills_list:
        # match whole words where possible
        pattern = r'\b' + re.escape(skill.lower()) + r'\b'
        if re.search(pattern, t):
            found.add(skill)
        else:
            # relax match: some skills like "node.js" -> "node"
            if skill.lower().replace('.', '') in t:
                if re.search(r'\b' + re.escape(skill.lower().replace('.', '')) + r'\b', t):
                    found.add(skill)
    return sorted(found)

def extract_years_of_experience(text: str) -> float:
    """Heuristic: find 'X years' or year ranges and estimate total years."""
    t = text.lower()
    # look for "X years" or "X+ years"
    m = re.findall(r'(\d+(?:\.\d+)?)\s*\+\s*years', t)
    if m:
        try:
            return float(m[0])
        except:
            pass
    m = re.findall(r'(\d+(?:\.\d+)?)\s*years', t)
    if m:
        # take max found
        try:
            vals = [float(x) for x in m]
            return max(vals)
        except:
            pass
    # look for year ranges like 2018-2022, 2018 to 2022
    ranges = re.findall(r'(\b19|20)\d{2}\s*(?:-|to)\s*(\b19|20)\d{2}', text)
    if ranges:
        # compute max span among found ranges
        spans = []
        for r in re.findall(r'((?:19|20)\d{2})\s*(?:-|to)\s*((?:19|20)\d{2})', text):
            try:
                start = int(r[0]); end = int(r[1])
                if end >= start:
                    spans.append(end - start)
            except:
                pass
        if spans:
            return float(max(spans))
    return 0.0

def extract_education(text: str) -> List[str]:
    """Very simple education extraction by keywords."""
    degrees = ["bachelor", "b.sc", "bsc", "b.tech", "be", "bs", "master", "m.sc", "msc", "m.tech", "mba", "phd", "doctor"]
    found = []
    t = text.lower()
    for d in degrees:
        if d in t:
            found.append(d)
    return sorted(set(found))

def parse_resume(path_or_text: str, is_file: bool = True, skill_file: str = None) -> Dict:
    """Return structured parse of a resume.
       If is_file True, treat path_or_text as file path; else treat as raw text.
    """
    if is_file:
        text = extract_text_from_pdf(path_or_text)
    else:
        text = path_or_text

    skills_list = load_skills(skill_file)
    skills = extract_skills(text, skills_list)
    years = extract_years_of_experience(text)
    edu = extract_education(text)
    sentences = sent_tokenize(text)
    short_summary = " ".join(sentences[:3]) if sentences else text[:200]

    return {
        "text": text,
        "summary": short_summary,
        "skills": skills,
        "years_experience": years,
        "education": edu
    }
