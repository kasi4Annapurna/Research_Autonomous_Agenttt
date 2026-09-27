# Autonomous Research Agent — Assessment Option 1

A production-minded autonomous research agent.

Core requirements:
- Accept a user query/topic.
- Search external sources.
- Extract relevant information.
- Remove duplicate/low-value content.
- Generate key points, important findings, references/sources, and actionable insights.

Bonus:
- LLM-generated search strategy.
- Parallel information gathering.
- Markdown/PDF export.
- Persistent search memory.
- FastAPI API.
- LangGraph orchestration.
- Source quality filtering.
- Evidence-grounded structured synthesis.
- Tests for deterministic components.

Architecture:
User Query -> Planner -> Parallel Search/Fetch -> Deduplicate/Filter -> Evidence Synthesis -> Markdown/PDF + Memory

Setup:
```cmd
py -3.12 -m venv venv
venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
copy .env.example .env
```

Add OPENAI_API_KEY and TAVILY_API_KEY to .env.

CLI:
```cmd
python main.py "What are the latest advances in agentic AI?"
python main.py "What are the latest advances in agentic AI?" --pdf
python main.py --memory
```

API:
```cmd
uvicorn app.api:app --reload
```
POST /research with {"query":"...", "export_pdf":false}.

Interview topics:
- Why LangGraph?
- Why parallel async I/O?
- Why preserve source URLs?
- How to defend against prompt injection in webpages?
- Retries/rate limits/timeouts?
- Scaling to 10,000 concurrent requests?
- Evaluation of factuality and source faithfulness?
- PostgreSQL/vector memory migration?
- Human approval for critical actions?
