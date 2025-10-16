from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from typing import Dict, List
import numpy as np

def compute_tfidf_similarity(resume_text: str, job_text: str, top_k:int=10) -> float:
    """Compute cosine similarity between resume and job using TF-IDF."""
    corpus = [resume_text, job_text]
    vectorizer = TfidfVectorizer(stop_words='english', max_features=5000)
    tfidf = vectorizer.fit_transform(corpus)
    sim = cosine_similarity(tfidf[0:1], tfidf[1:2])[0][0]
    return float(sim)

def score_by_skills(resume_skills: List[str], required_skills: List[str]) -> float:
    """Return skill overlap ratio (0..1)."""
    if not required_skills:
        return 0.0
    rs = set([s.lower() for s in resume_skills])
    rq = set([s.lower() for s in required_skills])
    if not rq:
        return 0.0
    inter = rs.intersection(rq)
    return float(len(inter)) / float(len(rq))

def compute_final_score(resume_text: str, resume_skills: List[str],
                        job_text: str, required_skills: List[str],
                        years_exp_resume: float, min_years_required: float = 0.0) -> Dict:
    """
    Weighted score:
      - semantic_sim (TF-IDF cosine) weight: 0.6
      - skill_overlap weight: 0.35
      - experience bonus/penalty weight: 0.05
    Returns score 0..100 and justification.
    """
    sem = compute_tfidf_similarity(resume_text, job_text)
    skill_overlap = score_by_skills(resume_skills, required_skills)

    # experience factor: if resume meets min years -> small bonus; else small penalty
    if min_years_required > 0:
        if years_exp_resume >= min_years_required:
            exp_factor = 1.0
        else:
            exp_factor = max(0.0, years_exp_resume / min_years_required)
    else:
        exp_factor = 1.0

    w_sem = 0.6
    w_skill = 0.35
    w_exp = 0.05

    combined = (w_sem * sem) + (w_skill * skill_overlap) + (w_exp * exp_factor)
    # normalize to 0-100
    score = round(float(combined) * 100, 2)

    justification = {
        "semantic_similarity": round(sem, 4),
        "skill_overlap": round(skill_overlap, 4),
        "experience_factor": round(exp_factor, 4),
        "weights": {"semantic": w_sem, "skill": w_skill, "experience": w_exp}
    }
    return {"score": score, "justification": justification}
