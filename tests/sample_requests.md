# Sample Requests for Smart Job Match Agent

## Sample Resume

```text
Aaryan Khanna
B.Tech in Computer Science — IIT Delhi (2023)

3 years of experience in software engineering and machine learning.

Experience:
- ML Engineer at TechStartup (2023-2026): Built recommendation systems using Python, PyTorch, and scikit-learn. Deployed models on AWS using Docker and MLOps pipelines. Worked with SQL databases for feature engineering.
- Backend Intern at FinCorp (2022): Developed REST APIs using FastAPI and PostgreSQL.

Skills: Python, PyTorch, scikit-learn, SQL, FastAPI, Docker, AWS, Git, MLOps, TensorFlow

Looking for: ML Engineer or Backend Engineer roles, preferably in Bangalore. Open to remote.
```

---

## 1. Health Check

```bash
curl http://localhost:8000/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "jobs_loaded": 50,
  "openai_key_set": true,
  "models": {
    "chat": "gpt-4o-mini",
    "embedding": "text-embedding-3-small"
  }
}
```

---

## 2. POST /recommend

```bash
curl -X POST http://localhost:8000/recommend \
  -H "Content-Type: application/json" \
  -d '{
    "resume_text": "Aaryan Khanna. B.Tech in Computer Science from IIT Delhi (2023). 3 years experience in Python, PyTorch, scikit-learn, SQL, FastAPI, Docker, AWS, Git, MLOps. Built recommendation systems at a tech startup. Developed REST APIs using FastAPI and PostgreSQL. Looking for ML Engineer or Backend Engineer roles in Bangalore. Open to remote."
  }'
```

**Expected Response Shape:**
```json
{
  "candidate": {
    "name": "Aaryan Khanna",
    "skills": ["Python", "PyTorch", "scikit-learn", "SQL", "FastAPI", "Docker", "AWS", "Git", "MLOps"],
    "experience_years": 3,
    "preferred_roles": ["ML Engineer", "Backend Engineer"],
    "education": "B.Tech in Computer Science from IIT Delhi"
  },
  "ranked_jobs": [
    {
      "id": 1,
      "title": "ML Engineer",
      "company": "DataCo",
      "location": "Bangalore",
      "remote": false,
      "domain": "Tech",
      "required_experience_years": 1,
      "salary_lpa": 12,
      "skills": ["Python", "PyTorch", "MLOps", "SQL", "scikit-learn"],
      "similarity_score": 0.8234,
      "explanation": "Strong match due to overlapping skills in Python, PyTorch, and MLOps..."
    }
    // ... 4 more jobs
  ],
  "clarifying_question": "Do you have a preference for company size — startup or established enterprise?"
}
```

---

## 3. POST /refine

```bash
curl -X POST http://localhost:8000/refine \
  -H "Content-Type: application/json" \
  -d '{
    "resume_text": "Aaryan Khanna. B.Tech in Computer Science from IIT Delhi (2023). 3 years experience in Python, PyTorch, scikit-learn, SQL, FastAPI, Docker, AWS, Git, MLOps. Built recommendation systems at a tech startup. Developed REST APIs using FastAPI and PostgreSQL. Looking for ML Engineer or Backend Engineer roles in Bangalore. Open to remote.",
    "clarifying_question": "Do you have a preference for company size — startup or established enterprise?",
    "candidate_answer": "I prefer working at startups because I enjoy wearing multiple hats and having direct impact on the product."
  }'
```

**Expected Response Shape:**
```json
{
  "ranked_jobs": [
    {
      "id": 1,
      "title": "ML Engineer",
      "company": "DataCo",
      "location": "Bangalore",
      "remote": false,
      "domain": "Tech",
      "required_experience_years": 1,
      "salary_lpa": 12,
      "skills": ["Python", "PyTorch", "MLOps", "SQL", "scikit-learn"],
      "similarity_score": 0.8456,
      "explanation": "Excellent fit — startup environment with ML focus matches your preference..."
    }
    // ... 4 more jobs
  ],
  "reasoning": "Based on your preference for startups, the rankings now favor smaller companies where you can have direct product impact. This shifted priority toward roles at DataCo and similar growth-stage companies."
}
```

---

## 4. Error Cases

### Empty resume
```bash
curl -X POST http://localhost:8000/recommend \
  -H "Content-Type: application/json" \
  -d '{"resume_text": ""}'
```
**Expected:** 422 Validation Error (min_length=1)

### Missing field
```bash
curl -X POST http://localhost:8000/recommend \
  -H "Content-Type: application/json" \
  -d '{}'
```
**Expected:** 422 Validation Error (resume_text required)
