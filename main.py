# app/main.py
import os
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, List
from . import parser, matcher, storage

app = FastAPI(title="Smart Resume Screener - Minimal")

# ensure DB
storage.init_db()

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

class MatchRequest(BaseModel):
    resume_text: Optional[str] = None
    resume_id: Optional[int] = None
    job_description: str
    required_skills: Optional[List[str]] = []
    min_years_required: Optional[float] = 0.0

@app.post("/parse")
async def parse_resume_endpoint(name: str = Form(...), file: UploadFile = File(...)):
    """Upload a resume PDF, parse it and store parsed JSON. Returns id + parsed data."""
    filename = file.filename
    save_path = os.path.join(UPLOAD_DIR, filename)
    with open(save_path, "wb") as f:
        f.write(await file.read())
    parsed = parser.parse_resume(save_path, is_file=True)
    rid = storage.save_parsed_resume(name=name, filename=filename, parsed=parsed)
    return JSONResponse({"id": rid, "parsed": parsed})

@app.post("/match")
async def match_endpoint(req: MatchRequest):
    """Match a resume (either raw text or stored id) with job description."""
    if req.resume_id:
        res = storage.get_resume(req.resume_id)
        if res is None:
            return JSONResponse({"error": "resume id not found"}, status_code=404)
        parsed = res["parsed"]
    elif req.resume_text:
        parsed = parser.parse_resume(req.resume_text, is_file=False)
    else:
        return JSONResponse({"error": "provide resume_id or resume_text"}, status_code=400)

    resume_text = parsed.get("text", "")
    resume_skills = parsed.get("skills", [])
    years = parsed.get("years_experience", 0.0)

    # required_skills taken from request
    required_skills = req.required_skills or []

    score_obj = matcher.compute_final_score(
        resume_text=resume_text,
        resume_skills=resume_skills,
        job_text=req.job_description,
        required_skills=required_skills,
        years_exp_resume=years,
        min_years_required=req.min_years_required or 0.0
    )
    out = {
        "candidate_parsed": parsed,
        "score": score_obj["score"],
        "justification": score_obj["justification"]
    }
    return JSONResponse(out)

@app.get("/resumes")
def list_resumes():
    return JSONResponse(storage.list_resumes())

@app.get("/")
def read_index():
    tpl_path = os.path.join(os.path.dirname(__file__), "templates", "index.html")
    if os.path.exists(tpl_path):
        with open(tpl_path, "r", encoding="utf-8") as f:
            return HTMLResponse(f.read())
    return HTMLResponse("<h3>Smart Resume Screener</h3><p>Use the API endpoints.</p>")
