# Smart Job Match Agent — Technical Writeup

## Design Choices

The Smart Job Match Agent is built as a single-file FastAPI application optimized for clarity, correctness, and Vercel-compatible serverless deployment. The entire API lives in `api/index.py`, which keeps the codebase easy to navigate and explain during a technical interview.

**FastAPI** was chosen as the framework because it provides automatic request validation via Pydantic, built-in OpenAPI documentation, and excellent async support — all with minimal boilerplate.

### Product-Oriented "Wow Factor": Interview Readiness Analysis

Beyond simple matching, I implemented an **Interview Readiness Analysis** layer. For every recommended job, the agent performs a gap analysis comparing the candidate's parsed profile against the specific job requirements. It returns:
- **Match Level:** (Strong, Moderate, or Stretch)
- **Readiness Score:** (0-100%)
- **Skill Gaps:** Specific missing competencies identified by the LLM.
- **Suggested Preparation:** Targeted advice on what to study or prepare for that specific job's interview.

This transforms the tool from a simple search engine into a career coach, providing immediate value to the user.

For **semantic search**, I use OpenAI's `text-embedding-3-small` model. This model was chosen over local alternatives like `sentence-transformers` for several practical reasons: it produces high-quality 1536-dimensional embeddings, requires no local GPU or large model downloads, has predictable latency, and works within Vercel's memory constraints (~256MB). Local models like `all-MiniLM-L6-v2` would require ~500MB+ of model weights and cause cold-start timeouts on serverless platforms. The trade-off is an external API dependency, which is acceptable for this use case.

Each job listing is converted into a rich text string combining title, company, location, remote status, domain, experience level, salary, skills, and description. This gives the embedding model maximum signal to work with. Cosine similarity is computed using NumPy — straightforward and fast for a 50-job dataset. Job embeddings are cached globally after the first request to avoid redundant API calls.

## Agentic Architecture

The system implements a genuine **LLM agentic layer** using OpenAI's native tool/function calling — not prompt-hacked JSON extraction. Two real tools are defined:

1. **`parse_resume`** — The LLM receives the resume text and decides to call this tool to extract structured candidate information (name, skills, experience, preferred roles, education). The tool execution then uses a separate LLM call with `response_format: json_object` to ensure reliable structured output.

2. **`explain_matches`** — After semantic ranking produces the top 5 jobs, the LLM calls this tool to generate per-job explanations and a dynamic clarifying question tailored to the candidate's profile.

The flow is explicitly agentic: the LLM is presented with tool definitions and chooses which to call. The application orchestrates the multi-step pipeline: **parse → rank → explain**. Tool calls are tracked in the conversation history, maintaining proper `tool` role messages, so the LLM has full context at each step.

The `/refine` endpoint extends this by combining the original resume with the candidate's answer to a clarifying question, re-computing semantic rankings with the enriched context, and generating new explanations that reflect the updated preferences.

## Honest Weaknesses

1. **Raw text only** — The API accepts plain text resumes. There is no PDF or DOCX parser, so candidates must paste their resume content. Adding `pymupdf` or `python-docx` would be a straightforward improvement.

2. **Small static dataset** — The 50-job dataset is loaded from a JSON file. In production, this would be replaced with a vector database (Pinecone, Weaviate, or pgvector) for scalable nearest-neighbor search.

3. **No vector database** — Embeddings are computed and stored in memory using NumPy arrays. This works for 50 jobs but would not scale. A proper vector DB would enable approximate nearest-neighbor search over millions of listings.

4. **OpenAI rate limits and cost** — Every request makes 2-4 OpenAI API calls (embedding + chat completions). Under heavy traffic, this could hit rate limits or accumulate costs quickly.

5. **Vercel cold starts** — Serverless functions on Vercel's free tier have a 10-second timeout. The first request after a cold start must load the dataset, compute job embeddings, and run multiple LLM calls, which can be tight.

6. **No evaluation harness** — There is no automated way to measure recommendation quality (precision, recall, NDCG). Without ground-truth labels, it's hard to know if the rankings are actually good.

7. **Embedding cache is ephemeral** — The job embedding cache resets on every cold start in serverless environments. A persistent cache (Redis or file-based) would eliminate redundant embedding calls.

## Next Steps

The highest-impact improvement would be an **evaluation harness with a feedback loop**. This would involve creating synthetic candidate-job pairs with known relevance scores, running the system against them, and measuring ranking quality. This turns subjective "does it feel right?" into measurable metrics.

Beyond evaluation, I would prioritize: (1) a **vector database** like Pinecone for scalable search, (2) **PDF resume parsing** to improve UX, (3) **streaming responses** for better perceived latency, and (4) a **caching layer** (Redis) for embeddings and parsed resumes to reduce API costs. A simple feedback mechanism where users rate recommendations would close the loop and enable continuous improvement.
