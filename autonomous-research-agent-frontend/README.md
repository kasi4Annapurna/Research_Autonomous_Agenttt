# ResearchOS — Autonomous Research Agent Frontend

A React + Vite interface for the existing FastAPI autonomous research agent.

## Run

From this folder:

```bash
npm install
npm run dev
```

Open:

http://localhost:5173

The Vite development server proxies `/api/*` to:

http://127.0.0.1:8000

So start the existing backend first:

```bash
uvicorn app.api:app --reload
```

Then start this frontend in a second terminal:

```bash
npm run dev
```

## Backend contract

The UI calls:

`POST /research`

with:

```json
{
  "query": "Your research goal",
  "export_pdf": true
}
```

and expects the existing response fields:

- `query`
- `search_queries`
- `report.key_points`
- `report.important_findings`
- `report.actionable_insights`
- `report.sources`
- `markdown_path`
- `pdf_path`
