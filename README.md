# Autonomous Research Agent

## Agentic AI Engineer Intern — Take-Home Assignment

An autonomous web research system that accepts a high-level research goal, decomposes it into focused research tasks, gathers information using web tools, evaluates the available evidence, conditionally performs additional research, and generates a structured research report.

The project is designed to demonstrate practical **agentic AI orchestration, tool usage, conditional reasoning, persistent memory, live execution monitoring, and report generation**.

---

# 1. Project Overview

A conventional LLM application typically follows:

```text
User Question
      ↓
LLM
      ↓
Answer
```

This project uses an autonomous workflow:

```text
Research Goal
      ↓
Planning
      ↓
Web Research
      ↓
Source Filtering
      ↓
Evidence Evaluation
      ↓
Agent Decision
      ↓
Research Again ───────┐
      ↓               │
Synthesis             │
      ↓               │
Export                │
      ↓               │
Memory                │
                      │
      └───────────────┘
```

The key idea is that the system does not immediately generate an answer after the first research pass.

It evaluates the collected evidence and can decide that another research round is necessary before synthesis.

---

# 2. Key Features

### Autonomous Research Planning

The agent receives a high-level research goal and generates multiple focused search queries.

### Tool-Based Research

The agent uses web research tools to gather information relevant to the generated queries.

### Source Filtering

Collected research results are cleaned, deduplicated, and filtered before being passed to the reasoning stages.

### Evidence Evaluation

The LLM evaluates whether the collected evidence is sufficient for the research objective.

### Conditional Research Loop

If evidence is insufficient, the workflow can branch back into another research round and generate additional research queries.

### Structured Synthesis

Once the evidence is considered sufficient, the agent produces a structured research report.

### Live Execution Monitoring

The React frontend displays the current stage of the research workflow while the backend is executing.

### Persistent Memory

Completed research sessions are stored using SQLite.

### Markdown and PDF Export

Research results can be exported as Markdown and optionally as PDF.

### Error Handling

The system handles common web-source and LLM failures while attempting to keep the overall research workflow operational.

---

# 3. Agentic Workflow

The core workflow is implemented using LangGraph.

```text
START
  │
  ▼
┌──────────────┐
│    PLAN      │
│ Generate     │
│ Research     │
│ Queries      │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│    GATHER    │
│ Search Web   │
│ Fetch Sources│
└──────┬───────┘
       │
       ▼
┌──────────────┐
│    CLEAN     │
│ Filter and   │
│ Deduplicate  │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│   EVALUATE   │
│ Is Evidence  │
│ Sufficient?  │
└──────┬───────┘
       │
   ┌───┴────┐
   │        │
  NO       YES
   │        │
   ▼        ▼
RESEARCH   SYNTHESIZE
AGAIN        │
   │         │
   └────┐    │
        │    ▼
        │  EXPORT
        │    │
        │    ▼
        └─► MEMORY
```

The most important agentic decision is:

```text
Research → Evaluate Evidence → Decide → Research Again if Needed
```

This allows the workflow to adapt based on the information collected.

---

# 4. Why It Is Agentic

The system is more than a simple LLM wrapper.

The agent autonomously performs several steps:

1. Receives a high-level goal.
2. Decomposes the goal into research queries.
3. Selects and invokes research tools.
4. Collects external information.
5. Filters the collected sources.
6. Evaluates evidence sufficiency.
7. Decides whether additional research is required.
8. Performs another research round when necessary.
9. Synthesizes the final report.
10. Persists the completed research session.

The strongest agentic behavior is the conditional research loop:

```text
Plan
 ↓
Search
 ↓
Evaluate
 ↓
Decision
 ↓
Research Again if Required
 ↓
Synthesize
```

The workflow therefore adapts to the research state instead of following only a fixed linear pipeline.

---

# 5. Technology Stack

## Backend

* Python
* FastAPI
* LangGraph
* LangChain
* Groq
* Pydantic
* SQLite

## Frontend

* React
* Vite
* JavaScript
* CSS

## LLM

The project uses a Groq-hosted LLM configured through environment variables.

Current configuration:

```text
openai/gpt-oss-120b
```

The model configuration can be changed without redesigning the overall workflow.

---

# 6. Project Structure

```text
autonomous-research-agent/
│
├── README.md
├── .gitignore
│
├── autonomous-research-agent-pro/
│   │
│   ├── app/
│   │   ├── agent/
│   │   │   ├── __init__.py
│   │   │   └── graph.py
│   │   │
│   │   ├── memory/
│   │   │   ├── __init__.py
│   │   │   └── store.py
│   │   │
│   │   ├── tools/
│   │   │   ├── __init__.py
│   │   │   ├── search.py
│   │   │   └── export.py
│   │   │
│   │   ├── api.py
│   │   ├── progress.py
│   │   └── schemas.py
│   │
│   ├── tests/
│   │   └── test_search.py
│   │
│   ├── data/
│   │
│   ├── exports/
│   │
│   ├── config.py
│   ├── main.py
│   ├── requirements.txt
│   ├── .env.example
│   └── README.md
│
└── autonomous-research-agent-frontend/
    │
    ├── src/
    │   ├── App.jsx
    │   ├── main.jsx
    │   └── styles.css
    │
    ├── index.html
    ├── package.json
    ├── package-lock.json
    ├── vite.config.js
    └── README.md
```

---

# 7. Backend Architecture

The backend is responsible for:

* Research orchestration
* LLM interaction
* Web research
* Evidence evaluation
* Research decisions
* Report synthesis
* Export
* Persistent memory
* Live progress tracking
* REST APIs

The main orchestration logic is located in:

```text
app/agent/graph.py
```

---

# 8. LangGraph Workflow

The workflow contains the following major nodes.

### Planning

```text
plan_research
```

Generates focused research queries from the user's research goal.

### Gathering

```text
gather_research
```

Executes web research and collects candidate sources.

### Cleaning

```text
clean_and_filter
```

Removes duplicate or unusable information and prepares source content.

### Evidence Evaluation

```text
evaluate_evidence
```

Uses the LLM to determine whether the available evidence is sufficient.

### Research Decision

```text
research_decision
```

Determines whether the workflow should synthesize the result or perform another research round.

### Additional Research

```text
research_again
```

Generates and executes another research round when necessary.

### Synthesis

```text
synthesize_report
```

Produces the final research report.

### Finalization

```text
finalize_report
```

Exports the report and saves the completed session to persistent memory.

---

# 9. State Management

The LangGraph state contains information such as:

```text
query
search_queries
raw_sources
sources
evidence_assessment
research_round
max_research_rounds
report
markdown
markdown_path
pdf_path
export_pdf
session_id
run_id
```

This allows information to move between workflow stages while maintaining the context of the research task.

---

# 10. Live Progress System

The backend contains a lightweight execution-progress system.

The frontend can poll:

```http
GET /research/status/{run_id}
```

The backend reports stages such as:

```text
1. Planning
2. Web Research
3. Source Filtering
4. Evidence Evaluation
5. Agent Decision
6. Synthesis
7. Export
8. Memory
```

This makes the agent execution visible to the user rather than exposing only the final response.

---

# 11. Frontend

The frontend is built with React and Vite.

The interface provides:

* Research goal input
* Export PDF option
* Example research questions
* Live workflow progress
* Research metrics
* Generated search queries
* Research sources
* Final report
* Markdown download
* PDF download
* Copy report functionality
* Reports section
* Memory section

The frontend communicates with the FastAPI backend through the `/api` proxy configured in Vite.

---

# 12. API Endpoints

## Health

```http
GET /health
```

Checks whether the backend is running.

## Start Research

```http
POST /research/start
```

Starts an asynchronous research execution and returns a `run_id`.

## Research Status

```http
GET /research/status/{run_id}
```

Returns the current execution status.

When completed, the response contains the final research result.

## Synchronous Research

```http
POST /research
```

Runs a research request directly.

## Memory

```http
GET /memory
GET /memory/count
GET /memory/{session_id}
DELETE /memory/{session_id}
DELETE /memory
```

## Reports

```http
GET /reports
GET /reports/{filename}
GET /reports/download?filename=...
GET /reports/pdf?filename=...
```

---

# 13. Persistent Memory

SQLite is used to store completed research sessions.

The stored information includes:

* Session ID
* Research query
* Generated report
* Search queries
* Source count
* Number of research rounds
* Markdown path
* PDF path
* Creation timestamp

The database is local to the prototype and is intentionally excluded from the Git repository.

---

# 14. Report Export

The export layer supports:

```text
Markdown
PDF
```

Reports are stored with unique filenames so previous research results are not overwritten.

The export implementation is located in:

```text
autonomous-research-agent-pro/app/tools/export.py
```

---

# 15. Setup

## Prerequisites

Install:

* Python 3.x
* Node.js
* npm
* Git

A Groq API key is also required.

---

## Backend Setup

Navigate to the backend:

```bash
cd autonomous-research-agent-pro
```

Create a virtual environment:

```bash
python -m venv venv
```

Activate it on Windows:

```bash
venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

If required:

```bash
pip install langchain-groq
```

---

# 16. Environment Variables

Create a local `.env` file.

Example:

```env
GROQ_API_KEY=your_groq_api_key_here
```

A safe template is provided as:

```text
.env.example
```

**Do not commit `.env` or API keys to GitHub.**

---

# 17. Run Backend

From:

```text
autonomous-research-agent-pro
```

run:

```bash
uvicorn app.api:app --reload
```

Backend:

```text
http://127.0.0.1:8000
```

Swagger API documentation:

```text
http://127.0.0.1:8000/docs
```

---

# 18. Run Frontend

Open another terminal.

Navigate to:

```bash
cd autonomous-research-agent-frontend
```

Install dependencies:

```bash
npm install
```

Start the development server:

```bash
npm run dev
```

The frontend will normally be available at:

```text
http://localhost:5173
```

---

# 19. Example Research Task

Example user goal:

```text
What are the major trends in agentic AI systems?
```

The agent can transform this into multiple research queries such as:

```text
Current agentic AI landscape
Major agentic AI architectures
Agent tool-use patterns
Agent memory approaches
Agentic AI limitations
Agent evaluation approaches
```

The system then gathers sources, evaluates evidence, and decides whether another research round is required.

---

# 20. Example Execution

```text
User
 │
 │ Research Goal
 ▼
React Frontend
 │
 ▼
FastAPI
 │
 ▼
LangGraph Agent
 │
 ├── Planning
 │
 ├── Web Research
 │
 ├── Source Filtering
 │
 ├── Evidence Evaluation
 │
 ├── Decision
 │      │
 │      ├── Evidence sufficient ──► Synthesis
 │      │
 │      └── Evidence insufficient
 │                    │
 │                    ▼
 │               Research Again
 │
 ├── Synthesis
 │
 ├── Export
 │
 └── SQLite Memory
```

---

# 21. Evaluation

The prototype was evaluated using workflow-level scenarios rather than treating the task as a conventional classification problem.

Test scenarios include:

```text
successful_run
insufficient_evidence
research_again
export_success
tool_error
```

These scenarios test:

* Successful end-to-end execution
* Evidence insufficiency
* Conditional research behavior
* Export functionality
* Error handling

---

# 22. Precision and Recall

Formal precision and recall metrics are not reported for the current prototype.

The reason is that this system is primarily an autonomous research and synthesis workflow rather than a conventional classification model, and the prototype does not currently have a sufficiently large manually labeled ground-truth dataset.

A production evaluation framework should establish a benchmark dataset and measure:

* Retrieval precision
* Retrieval recall
* Evidence relevance
* Citation correctness
* Factual consistency
* Report completeness
* Research latency
* Token usage
* Cost per research task

---

# 23. Synthetic Test Traces

Synthetic traces were created to exercise different workflow paths.

Labels include:

```text
successful_run
insufficient_evidence
research_again
export_success
tool_error
```

These traces are synthetic development/evaluation data and are not presented as real user activity.

---

# 24. Limitations

This is a functional agentic prototype and not a production-scale research platform.

Known limitations include:

* Web sources may be unavailable.
* Some websites may block automated access.
* Search results may contain incomplete or low-quality information.
* Web requests may encounter rate limits or HTTP errors.
* LLM-based evidence evaluation is not formal fact verification.
* The research loop is intentionally bounded.
* SQLite is not intended for large-scale concurrent workloads.
* The system cannot guarantee that every generated statement is factually correct.
* Production-grade authentication and authorization are not included.

---

# 25. Production Roadmap

## Research Quality

* Source credibility scoring
* Citation verification
* Cross-source contradiction detection
* Automated factuality checks
* Human review for high-impact research

## Reliability

* Retry policies
* Timeouts
* Circuit breakers
* Better tool recovery
* Distributed task execution

## Infrastructure

* PostgreSQL
* Redis
* Background job queues
* Distributed workers
* Object storage

## Security

* Authentication
* Authorization
* Secret management
* Rate limiting
* Improved input validation

## Observability

* Structured logging
* Distributed tracing
* Token monitoring
* Cost monitoring
* Latency monitoring
* Agent execution metrics

## Evaluation

* Larger benchmark datasets
* Human-labeled evidence
* Retrieval precision/recall
* Citation validation
* Factual consistency evaluation
* Regression testing

---

# 26. Security

Never commit secrets to the repository.

The following files/directories should remain local:

```text
.env
venv/
node_modules/
data/*.db
exports/*.pdf
exports/*.md
```

The repository provides `.env.example` as a safe configuration template.

---

# 27. Design Philosophy

The project focuses on making the agent:

### Autonomous

The system decides how to decompose and continue the research process.

### Observable

The frontend exposes the current execution stage.

### Bounded

The research loop has limits to prevent uncontrolled execution and excessive token usage.

### Persistent

Completed research sessions can be retrieved from SQLite.

### Extensible

The LangGraph architecture makes it possible to add additional tools, research strategies, evaluators, and memory mechanisms.

---

# 28. Core Agentic Loop

The central design can be summarized as:

```text
GOAL
  ↓
PLAN
  ↓
ACT
  ↓
OBSERVE
  ↓
EVALUATE
  ↓
DECIDE
  ↓
┌─────────────────────────────┐
│ More research necessary?    │
└──────────────┬──────────────┘
               │
        YES ───┘
         │
         ▼
      ACT AGAIN
         │
         └──────────────► EVALUATE

        NO
         │
         ▼
     SYNTHESIZE
         │
         ▼
       EXPORT
         │
         ▼
       MEMORY
```

This loop is the main mechanism demonstrating autonomous behavior in the project.

---

# 29. Author

**Kasi Annapurna**

Agentic AI Engineer Intern — Take-Home Assignment

---
