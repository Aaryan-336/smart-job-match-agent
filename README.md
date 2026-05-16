# 🎯 Smart Job Match Agent

An AI-powered job recommendation API that uses **semantic search** (OpenAI embeddings + cosine similarity) and an **LLM agentic layer** (GPT-4o-mini with real tool/function calling) to match candidates with the best jobs from a curated dataset.

## Key Features

- **Agentic Pipeline:** Multi-step tool-calling architecture (`parse_resume` → `rank` → `explain_matches`).
- **Interview Readiness Analysis:** For each match, the agent estimates a readiness score (0-100), identifies specific skill gaps, and suggests actionable interview preparation steps.
- **Semantic Ranking:** Cosine similarity using state-of-the-art embeddings.
- **Minimal Professional UI:** Clean, developer-centric interface for easy interaction.
- **FastAPI Backend:** Fully validated request/response flow with Pydantic.
- **Vercel Native:** Optimized for serverless deployment with a single file architecture.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      POST /recommend                        │
│                                                             │
│  Resume Text                                                │
│      │                                                      │
│      ▼                                                      │
│  ┌──────────────────┐                                       │
│  │  LLM Agent Call   │──► Tool: parse_resume                │
│  │  (gpt-4o-mini)    │    → Extracts structured candidate   │
│  └──────────────────┘                                       │
│      │                                                      │
│      ▼                                                      │
│  ┌──────────────────┐                                       │
│  │  Semantic Ranker  │  text-embedding-3-small              │
│  │  Cosine Similarity│  Embed resume + 50 jobs              │
│  └──────────────────┘  Return top 5 by score                │
│      │                                                      │
│      ▼                                                      │
│  ┌──────────────────┐                                       │
│  │  LLM Agent Call   │──► Tool: explain_matches             │
│  │  (gpt-4o-mini)    │    → Explains each match             │
│  └──────────────────┘    → Asks clarifying question         │
│      │                                                      │
│      ▼                                                      │
│  Final JSON Response                                        │
└─────────────────────────────────────────────────────────────┘
```

## Quick Setup (5 commands)

```bash
# 1. Clone the repo
git clone <your-repo-url> && cd smart-job-match-agent

# 2. Create virtual environment
python -m venv venv && source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment variables
cp .env.example .env
# Edit .env and add your OpenAI API key

# 5. Run the server
uvicorn api.index:app --reload --port 8000
```

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | ✅ | — | Your OpenAI API key |
| `OPENAI_CHAT_MODEL` | ❌ | `gpt-4o-mini` | Chat model for tool calling |
| `OPENAI_EMBEDDING_MODEL` | ❌ | `text-embedding-3-small` | Embedding model for semantic search |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | API info and available endpoints |
| `GET` | `/health` | Health check with config status |
| `POST` | `/recommend` | Get job recommendations from resume |
| `POST` | `/refine` | Refine recommendations with follow-up |

## Sample Usage

### Get Recommendations

```bash
curl -X POST http://localhost:8000/recommend \
  -H "Content-Type: application/json" \
  -d '{
    "resume_text": "Aaryan Khanna. 3 years experience in Python, FastAPI, and machine learning. Built recommendation systems at a fintech startup. B.Tech in Computer Science from IIT Delhi. Skills: Python, PyTorch, SQL, Docker, AWS, scikit-learn. Looking for ML Engineer or Backend Engineer roles in Bangalore."
  }'
```

### Refine Recommendations

```bash
curl -X POST http://localhost:8000/refine \
  -H "Content-Type: application/json" \
  -d '{
    "resume_text": "Aaryan Khanna. 3 years experience in Python, FastAPI, and machine learning. Built recommendation systems at a fintech startup. B.Tech in Computer Science from IIT Delhi. Skills: Python, PyTorch, SQL, Docker, AWS, scikit-learn. Looking for ML Engineer or Backend Engineer roles in Bangalore.",
    "clarifying_question": "Do you prefer remote work or are you open to on-site roles?",
    "candidate_answer": "I strongly prefer remote work to maintain work-life balance."
  }'
```

## Vercel Deployment

```bash
# 1. Install Vercel CLI
npm i -g vercel

# 2. Login
vercel login

# 3. Deploy (set OPENAI_API_KEY in Vercel dashboard → Settings → Environment Variables)
vercel --prod
```

> **Important:** Add `OPENAI_API_KEY` as an environment variable in the Vercel project settings before deploying.

## Testing the Live API

```bash
# Health check
curl https://your-project.vercel.app/health

# Get recommendations
curl -X POST https://your-project.vercel.app/recommend \
  -H "Content-Type: application/json" \
  -d '{"resume_text": "Your resume text here..."}'
```

## Limitations

- **Raw text only** — no PDF/DOCX parsing; resume must be submitted as plain text.
- **Small dataset** — uses a curated 50-job dataset, not a live job board.
- **No vector database** — embeddings are computed in-memory; works fine for 50 jobs but won't scale to millions.
- **OpenAI dependency** — requires a valid API key; subject to rate limits and costs.
- **Vercel timeout** — serverless functions have a 10s timeout on the free tier; cold starts may be slow.
- **No persistent state** — job embedding cache resets on each cold start.

## Tech Stack

- **Python** + **FastAPI** — lightweight, async-ready web framework
- **OpenAI API** — `text-embedding-3-small` for embeddings, `gpt-4o-mini` for tool calling
- **NumPy** — cosine similarity computation
- **Pydantic** — request/response validation
- **Vercel** — serverless deployment
