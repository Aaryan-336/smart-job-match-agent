"""
Smart Job Match Agent — FastAPI Application
Now supports Gemini (Google Generative AI) for free usage.
Uses Gemini embeddings + cosine similarity for semantic ranking,
and Gemini 1.5 Flash for agentic behavior.
"""

import os
import json
import time
from pathlib import Path
from typing import Optional, Union

import re
import asyncio
import numpy as np
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from openai import OpenAI
from google import genai
from google.genai import types

# ── Load environment ─────────────────────────────────────────────────────────
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Default models
OPENAI_CHAT_MODEL = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini")
OPENAI_EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
GEMINI_CHAT_MODEL = os.getenv("GEMINI_CHAT_MODEL", "gemini-2.0-flash")
GEMINI_EMBEDDING_MODEL = os.getenv("GEMINI_EMBEDDING_MODEL", "gemini-embedding-001")

# Determine provider
PROVIDER = "gemini" if GEMINI_API_KEY else "openai"

# ── FastAPI app ──────────────────────────────────────────────────────────────
app = FastAPI(
    title="Smart Job Match Agent",
    description="AI-powered job recommendation API using semantic search and LLM tool calling.",
    version="1.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Pydantic models ─────────────────────────────────────────────────────────

class RecommendRequest(BaseModel):
    resume_text: str = Field(..., min_length=1, description="Raw resume text")

class RefineRequest(BaseModel):
    resume_text: str = Field(..., min_length=1)
    clarifying_question: str = Field(..., min_length=1)
    candidate_answer: str = Field(..., min_length=1)

class Candidate(BaseModel):
    name: str
    skills: list[str]
    experience_years: float
    preferred_roles: list[str]
    education: str

class RankedJob(BaseModel):
    id: int
    title: str
    company: str
    location: str
    remote: bool
    domain: str
    required_experience_years: int
    salary_lpa: float
    skills: list[str]
    similarity_score: float
    explanation: str
    # Interview Readiness Analysis
    match_level: str
    interview_readiness_score: int
    skill_gaps: list[str]
    suggested_preparation: list[str]

class RecommendResponse(BaseModel):
    candidate: Candidate
    ranked_jobs: list[RankedJob]
    clarifying_question: str

class RefineResponse(BaseModel):
    ranked_jobs: list[RankedJob]
    reasoning: str

# ── Load job dataset ─────────────────────────────────────────────────────────

def load_jobs() -> list[dict]:
    """Load jobs from job_dataset.json, trying multiple paths for Vercel compatibility."""
    possible_paths = [
        Path(__file__).resolve().parent / "job_dataset.json",         # api/ folder (preferred)
        Path(__file__).resolve().parent.parent / "job_dataset.json",  # root
        Path("job_dataset.json"),                                     # cwd
    ]
    for path in possible_paths:
        if path.exists():
            with open(path, "r") as f:
                jobs = json.load(f)
            if not isinstance(jobs, list) or len(jobs) == 0:
                raise RuntimeError(f"job_dataset.json is empty or malformed at {path}")
            return jobs
    raise FileNotFoundError(
        f"job_dataset.json not found. Tried: {[str(p) for p in possible_paths]}"
    )

JOBS: list[dict] = load_jobs()

# ── Global embedding cache ───────────────────────────────────────────────────
_job_embeddings_cache: Optional[np.ndarray] = None


def _get_openai_client() -> OpenAI:
    if not OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY not set.")
    return OpenAI(api_key=OPENAI_API_KEY)


def _get_gemini_client() -> genai.Client:
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY not set.")
    return genai.Client(api_key=GEMINI_API_KEY)


class RateLimitError(Exception):
    """Custom exception for rate limits to trigger fallback logic."""
    pass


def _call_gemini_with_retry(func, *args, **kwargs):
    """
    Helper to call Gemini API with retries for 429 Resource Exhausted errors.
    If limit is too high, raises RateLimitError to trigger deterministic fallback.
    """
    max_retries = 2  # Reduced for Vercel
    for i in range(max_retries):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            err_str = str(e).lower()
            if "429" in err_str or "resource_exhausted" in err_str or "quota" in err_str:
                if i < max_retries - 1:
                    wait_time = 2.0  # Constant short wait for Vercel
                    match = re.search(r"retry in ([\d\.]+)", err_str)
                    if match:
                        try:
                            wait_time = min(float(match.group(1)), 3.0) # Max 3s wait
                        except ValueError: pass
                    
                    if wait_time > 3.0: # If provider asks for too much time
                        raise RateLimitError(f"Rate limited by provider. Using fallback.")
                    
                    print(f"[Gemini] Rate limited. Retrying in {wait_time:.1f}s... (Attempt {i+1})")
                    time.sleep(wait_time)
                    continue
                else:
                    raise RateLimitError("Rate limit exceeded after retries.")
            raise e


# ── Embedding helpers ────────────────────────────────────────────────────────

def _build_job_text(job: dict) -> str:
    skills_str = ", ".join(job.get("skills", []))
    remote_str = "Remote" if job.get("remote") else "On-site"
    return (
        f"{job['title']} at {job['company']}. "
        f"Location: {job['location']} ({remote_str}). "
        f"Domain: {job.get('domain', 'N/A')}. "
        f"Required experience: {job.get('experience_years', 0)} years. "
        f"Salary: {job.get('salary_lpa', 0)} LPA. "
        f"Skills: {skills_str}. "
        f"Description: {job.get('description', '')}"
    )


def _get_embeddings(texts: list[str]) -> np.ndarray:
    """Get embeddings for a list of texts using the selected provider."""
    if PROVIDER == "gemini":
        client = _get_gemini_client()
        response = _call_gemini_with_retry(
            client.models.embed_content,
            model=GEMINI_EMBEDDING_MODEL,
            contents=texts,
            config=types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT")
        )
        # Handle both single and multiple outputs
        if len(texts) == 1:
            return np.array([response.embeddings[0].values])
        return np.array([e.values for e in response.embeddings])
    else:
        client = _get_openai_client()
        response = client.embeddings.create(input=texts, model=OPENAI_EMBEDDING_MODEL)
        return np.array([item.embedding for item in response.data])


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    a_norm = a / (np.linalg.norm(a) + 1e-9)
    b_norms = b / (np.linalg.norm(b, axis=1, keepdims=True) + 1e-9)
    return np.dot(b_norms, a_norm)


def _get_job_embeddings() -> np.ndarray:
    global _job_embeddings_cache
    if _job_embeddings_cache is None:
        # Try loading pre-calculated embeddings from disk
        possible_paths = [
            Path(__file__).resolve().parent / "job_embeddings.json",
            Path(__file__).resolve().parent.parent / "job_embeddings.json",
            Path("job_embeddings.json"),
        ]
        for path in possible_paths:
            if path.exists():
                try:
                    with open(path, "r") as f:
                        data = json.load(f)
                        _job_embeddings_cache = np.array(data)
                        print(f"[Init] Loaded job embeddings from {path}")
                        return _job_embeddings_cache
                except Exception as e:
                    print(f"[Init] Failed to load embeddings from {path}: {e}")

        # Fallback to API if file not found
        job_texts = [_build_job_text(job) for job in JOBS]
        _job_embeddings_cache = _get_embeddings(job_texts)
    return _job_embeddings_cache


def _parse_experience(val) -> float:
    """Robustly parse experience strings like '5+' or '2-3 years' into a float."""
    if isinstance(val, (int, float)):
        return float(val)
    if not val:
        return 0.0
    try:
        # Extract the first number found in the string
        match = re.search(r"([\d\.]+)", str(val))
        if match:
            return float(match.group(1))
    except Exception:
        pass
    return 0.0

def _get_fallback_embeddings(texts: list[str]) -> np.ndarray:
    """Mock embeddings for critical fallback when provider is down."""
    print("[Embed] Provider rate limited. Using zero-vector fallback for ranking.")
    return np.zeros((len(texts), 768)) # Common embedding dimension


def rank_jobs(resume_text: str, top_k: int = 5) -> list[tuple[dict, float]]:
    try:
        resume_embedding = _get_embeddings([resume_text])[0]
    except RateLimitError:
        # If even embedding fails, we just take the first K jobs (degraded mode)
        return [(JOBS[i], 0.5) for i in range(min(top_k, len(JOBS)))]
    
    job_embeddings = _get_job_embeddings()
    scores = _cosine_similarity(resume_embedding, job_embeddings)
    top_indices = np.argsort(scores)[::-1][:top_k]
    return [(JOBS[i], round(float(scores[i]), 4)) for i in top_indices]


# ── LLM Helpers ─────────────────────────────────────────────────────────────

def _generate_json(prompt: str, system_instruction: str = "") -> dict:
    """Generate structured JSON from LLM regardless of provider."""
    if PROVIDER == "gemini":
        client = _get_gemini_client()
        response = _call_gemini_with_retry(
            client.models.generate_content,
            model=GEMINI_CHAT_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json"
            )
        )
        return json.loads(response.text)
    else:
        client = _get_openai_client()
        response = client.chat.completions.create(
            model=OPENAI_CHAT_MODEL,
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
        )
        return json.loads(response.choices[0].message.content)


def _execute_parse_and_explain(resume_text: str, top_jobs: list[dict]) -> dict:
    system = "You are a recruitment assistant. Parse the resume AND analyze job matches concisely."
    prompt = (
        f"Resume: {resume_text}\n"
        f"Top Jobs: {json.dumps(top_jobs)}\n"
        "Return ONLY JSON with:\n"
        "1. 'candidate': {name, skills, experience_years, preferred_roles, education}\n"
        "2. 'explanations': list of {job_id, explanation (max 15 words), match_level, interview_readiness_score, skill_gaps, suggested_preparation}\n"
        "3. 'clarifying_question': (one brief question)\n"
        "4. 'reasoning': (briefly explain why these were picked if relevant)"
    )
    try:
        return _generate_json(prompt, system)
    except RateLimitError:
        print("[Agent] LLM Rate limit hit. Using deterministic fallback.")
        return _fallback_analysis(resume_text, top_jobs)
    except Exception as e:
        print(f"[Agent] LLM call failed ({type(e).__name__}). Using fallback.")
        return _fallback_analysis(resume_text, top_jobs)


def _fallback_analysis(resume_text: str, top_jobs: list[dict]) -> dict:
    """Deterministic fallback logic when LLM is unavailable."""
    # 1. Simple Resume Parsing (Regex)
    name_match = re.search(r"^([A-Z][a-z]+ [A-Z][a-z]+)", resume_text)
    name = name_match.group(1) if name_match else "Candidate"
    
    # Extract years (e.g. "5+ years" or "2 years")
    years_match = re.search(r"(\d+)\+?\s*years?", resume_text, re.I)
    exp_years = float(years_match.group(1)) if years_match else 2.0
    
    # Skill extraction (Look for common tech keywords)
    common_tech = {"python", "javascript", "react", "fastapi", "docker", "aws", "sql", "java", "node", "typescript", "nlp", "llm"}
    found_skills = [s for s in common_tech if s in resume_text.lower()]
    if not found_skills: found_skills = ["Software Development", "Problem Solving"]

    candidate = {
        "name": name,
        "skills": found_skills,
        "experience_years": exp_years,
        "preferred_roles": ["Software Engineer"],
        "education": "Degree in Computer Science or related field"
    }

    # 2. Match Explanations
    explanations = []
    for job in top_jobs:
        job_skills = {s.lower() for s in job.get("skills", [])}
        cand_skills = {s.lower() for s in found_skills}
        overlap = job_skills.intersection(cand_skills)
        gaps = job_skills - cand_skills
        
        overlap_ratio = len(overlap) / len(job_skills) if job_skills else 0.5
        exp_req = _parse_experience(job.get("experience_years", 0))
        exp_match = exp_years >= exp_req
        
        # Deterministic Score (0-100)
        score = int((overlap_ratio * 70) + (10 if exp_match else 0) + 20)
        score = min(95, max(40, score))
        
        level = "Strong Match" if score >= 80 else "Moderate Match" if score >= 60 else "Stretch Role"
        
        explanations.append({
            "job_id": job["id"],
            "explanation": f"Matches {len(overlap)} key skills. {level} based on profile overlap.",
            "match_level": level,
            "interview_readiness_score": score,
            "skill_gaps": list(gaps)[:3] if gaps else ["No major gaps"],
            "suggested_preparation": [f"Review {s} fundamentals" for s in list(gaps)[:2]] or ["Review system design"]
        })

    # 3. Dynamic Fallback Question
    remote_jobs = [j for j in top_jobs if j.get("remote")]
    if len(remote_jobs) > len(top_jobs) / 2:
        question = "Since many matches are remote, do you have a strong preference for remote work?"
    elif "ai" in resume_text.lower() or "llm" in resume_text.lower():
        question = "Are you specifically looking for roles involving Generative AI or NLP?"
    else:
        question = "What are your top 3 priorities in your next role (e.g., tech stack, culture, salary)?"

    return {
        "candidate": candidate,
        "explanations": explanations,
        "clarifying_question": question,
        "reasoning": "Determined using skill-overlap and experience matching logic (Fallback mode)."
    }


# ── Agentic Flow ────────────────────────────────────────────────────────────

async def run_agent(resume_text: str) -> dict:
    # 1. Rank jobs first (Fast)
    loop = asyncio.get_event_loop()
    ranked = await loop.run_in_executor(None, rank_jobs, resume_text, 3)
    
    top_jobs_for_llm = [
        {"id": j["id"], "title": j["title"], "company": j["company"], "skills": j["skills"]}
        for j, s in ranked
    ]

    # 2. Unified Parse + Explain
    result = await loop.run_in_executor(None, _execute_parse_and_explain, resume_text, top_jobs_for_llm)
    
    candidate = result.get("candidate", {})
    explanation_map = {e["job_id"]: e for e in result.get("explanations", [])}
    
    ranked_jobs = []
    for job, score in ranked:
        analysis = explanation_map.get(job["id"], {})
        # Ensure experience is a float for RankedJob
        exp = _parse_experience(job.get("experience_years", 0))
        ranked_jobs.append(
            RankedJob(
                **{**job, "experience_years": exp}, # Spread and override
                required_experience_years=int(exp),
                similarity_score=score,
                explanation=analysis.get("explanation", "Strong profile match."),
                match_level=analysis.get("match_level", "Moderate Match"),
                interview_readiness_score=analysis.get("interview_readiness_score", 70),
                skill_gaps=analysis.get("skill_gaps", []),
                suggested_preparation=analysis.get("suggested_preparation", ["Review core requirements"])
            )
        )

    # Robust candidate parsing
    candidate["experience_years"] = _parse_experience(candidate.get("experience_years", 0))
    
    return {
        "candidate": Candidate(**candidate),
        "ranked_jobs": ranked_jobs,
        "clarifying_question": result.get("clarifying_question", "What's your ideal role?")
    }


# ── API Endpoints ────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
def root():
    from api.ui import HTML_TEMPLATE
    html = HTML_TEMPLATE.replace("JOBS_LOADED_COUNT", str(len(JOBS)))
    chat_label = "gemini-flash-latest" if PROVIDER == "gemini" else OPENAI_CHAT_MODEL
    embed_label = "gemini-embedding-001" if PROVIDER == "gemini" else OPENAI_EMBEDDING_MODEL
    html = html.replace("gpt-4o-mini", chat_label)
    html = html.replace("text-embedding-3-small", embed_label)
    return HTMLResponse(content=html)


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "provider": PROVIDER,
        "jobs_loaded": len(JOBS),
        "openai_key_set": bool(OPENAI_API_KEY),
        "gemini_key_set": bool(GEMINI_API_KEY),
    }


@app.post("/recommend", response_model=RecommendResponse)
async def recommend(request: RecommendRequest):
    try:
        result = await run_agent(request.resume_text)
        return RecommendResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/refine", response_model=RefineResponse)
async def refine(request: RefineRequest):
    try:
        enriched_resume = f"{request.resume_text}\nQ: {request.clarifying_question}\nA: {request.candidate_answer}"
        
        loop = asyncio.get_event_loop()
        ranked = await loop.run_in_executor(None, rank_jobs, enriched_resume, 3)
        
        top_jobs_for_llm = [{"id": j["id"], "title": j["title"], "company": j["company"]} for j, s in ranked]
        
        # Consolidated Parse + Explain
        result = await loop.run_in_executor(None, _execute_parse_and_explain, enriched_resume, top_jobs_for_llm)
        explanation_map = {e["job_id"]: e for e in result.get("explanations", [])}

        ranked_jobs = []
        for j, s in ranked:
            analysis = explanation_map.get(j["id"], {})
            exp = _parse_experience(j.get("experience_years", 0))
            ranked_jobs.append(
                RankedJob(
                    **{**j, "experience_years": exp},
                    required_experience_years=int(exp),
                    similarity_score=s,
                    explanation=analysis.get("explanation", "Matched."),
                    match_level=analysis.get("match_level", "Moderate Match"),
                    interview_readiness_score=analysis.get("interview_readiness_score", 70),
                    skill_gaps=analysis.get("skill_gaps", []),
                    suggested_preparation=analysis.get("suggested_preparation", ["Review core requirements"])
                )
            )

        return RefineResponse(
            ranked_jobs=ranked_jobs, 
            reasoning=result.get("reasoning", "Updated based on feedback.")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
