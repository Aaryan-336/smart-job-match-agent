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
GEMINI_CHAT_MODEL = os.getenv("GEMINI_CHAT_MODEL", "gemini-flash-latest")
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
        Path(__file__).resolve().parent.parent / "job_dataset.json",  # local dev
        Path(__file__).resolve().parent / "job_dataset.json",         # fallback
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


def _call_gemini_with_retry(func, *args, **kwargs):
    """
    Helper to call Gemini API with retries for 429 Resource Exhausted errors.
    Parses 'retry in X seconds' from the error message.
    """
    max_retries = 3
    for i in range(max_retries):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            err_str = str(e).lower()
            # Check for 429 or Resource Exhausted
            if "429" in err_str or "resource_exhausted" in err_str:
                if i < max_retries - 1:
                    # Default backoff
                    wait_time = (i + 1) * 5
                    
                    # Try to extract precise wait time from error message
                    # Example: "Please retry in 42.093158764s."
                    match = re.search(r"retry in ([\d\.]+)", err_str)
                    if match:
                        try:
                            wait_time = float(match.group(1)) + 1.0  # Add 1s buffer
                        except ValueError:
                            pass
                    
                    print(f"[Gemini] Rate limited. Retrying in {wait_time:.2f}s... (Attempt {i+1}/{max_retries})")
                    time.sleep(wait_time)
                    continue
            # Re-raise if not 429 or all retries failed
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
            Path(__file__).resolve().parent.parent / "job_embeddings.json",
            Path(__file__).resolve().parent / "job_embeddings.json",
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


def rank_jobs(resume_text: str, top_k: int = 5) -> list[tuple[dict, float]]:
    resume_embedding = _get_embeddings([resume_text])[0]
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


def _execute_parse_resume(resume_text: str) -> dict:
    system = (
        "You are a resume parser. Extract structured information. "
        "Return ONLY valid JSON with: name, skills (array), experience_years (number), "
        "preferred_roles (array), education (string)."
    )
    return _generate_json(resume_text, system)


def _execute_explain_matches(candidate: dict, top_jobs: list[dict]) -> dict:
    system = "You are a career advisor AI. Be concise and professional."
    prompt = (
        f"Candidate: {json.dumps(candidate)}\n"
        f"Jobs: {json.dumps(top_jobs)}\n"
        "Analyze matches and return ONLY JSON with: 'explanations' (array of {job_id, explanation (1-2 sentences), "
        "match_level (Strong/Moderate/Stretch), interview_readiness_score (0-100), skill_gaps (list), "
        "suggested_preparation (list of 2 items)}) and 'clarifying_question'."
    )
    return _generate_json(prompt, system)


# ── Agentic Flow ────────────────────────────────────────────────────────────

async def run_agent(resume_text: str) -> dict:
    # 1 & 2. Parse and Rank in parallel
    loop = asyncio.get_event_loop()
    parse_task = loop.run_in_executor(None, _execute_parse_resume, resume_text)
    rank_task = loop.run_in_executor(None, rank_jobs, resume_text, 5)
    
    candidate, ranked = await asyncio.gather(parse_task, rank_task)
    
    top_jobs_for_llm = [
        {
            "id": job["id"],
            "title": job["title"],
            "company": job["company"],
            "skills": job["skills"],
            "similarity_score": score,
        }
        for job, score in ranked
    ]

    # 3. Explain
    explanations_result = await loop.run_in_executor(None, _execute_explain_matches, candidate, top_jobs_for_llm)

    # 4. Build response
    explanation_map = {e["job_id"]: e for e in explanations_result.get("explanations", [])}
    
    ranked_jobs = []
    for job, score in ranked:
        analysis = explanation_map.get(job["id"], {})
        ranked_jobs.append(
            RankedJob(
                **job,
                required_experience_years=job.get("experience_years", 0),
                similarity_score=score,
                explanation=analysis.get("explanation", "Strong profile match."),
                match_level=analysis.get("match_level", "Moderate Match"),
                interview_readiness_score=analysis.get("interview_readiness_score", 70),
                skill_gaps=analysis.get("skill_gaps", []),
                suggested_preparation=analysis.get("suggested_preparation", ["Review core requirements"])
            )
        )

    return {
        "candidate": Candidate(**candidate),
        "ranked_jobs": ranked_jobs,
        "clarifying_question": explanations_result.get("clarifying_question", "What's your ideal role?")
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
        rank_task = loop.run_in_executor(None, rank_jobs, enriched_resume, 5)
        parse_task = loop.run_in_executor(None, _execute_parse_resume, enriched_resume)
        
        ranked, candidate = await asyncio.gather(rank_task, parse_task)
        
        top_jobs_for_llm = [{"id": j["id"], "title": j["title"], "similarity_score": s} for j, s in ranked]
        
        explanations_result = await loop.run_in_executor(None, _execute_explain_matches, candidate, top_jobs_for_llm)
        explanation_map = {e["job_id"]: e for e in explanations_result.get("explanations", [])}

        ranked_jobs = []
        for j, s in ranked:
            analysis = explanation_map.get(j["id"], {})
            ranked_jobs.append(
                RankedJob(
                    **j,
                    required_experience_years=j.get("experience_years", 0),
                    similarity_score=s,
                    explanation=analysis.get("explanation", "Matched."),
                    match_level=analysis.get("match_level", "Moderate Match"),
                    interview_readiness_score=analysis.get("interview_readiness_score", 70),
                    skill_gaps=analysis.get("skill_gaps", []),
                    suggested_preparation=analysis.get("suggested_preparation", ["Review core requirements"])
                )
            )

        reasoning_result = await loop.run_in_executor(
            None, 
            _generate_json,
            f"Explain how answer '{request.candidate_answer}' changed recommendations for {request.resume_text[:100]}...",
            "You are a career advisor. Return JSON with 'reasoning' (string)."
        )

        return RefineResponse(ranked_jobs=ranked_jobs, reasoning=reasoning_result.get("reasoning", "Updated based on feedback."))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
