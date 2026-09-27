from pathlib import Path
from threading import Thread
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, PlainTextResponse
from pydantic import BaseModel

from app.agent.graph import run_research
from app.progress import (
    create_run,
    get_run,
    complete_run,
    fail_run,
)
from app.memory.store import (
    load as load_memory,
    get_session,
    delete_session,
    clear_all,
    count_sessions,
)


# ============================================================
# APP
# ============================================================

app = FastAPI(
    title="Autonomous Research Agent",
    description="Agentic AI research system",
    version="1.0.0",
)


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
EXPORT_DIR = BASE_DIR / "exports"


# ============================================================
# REQUEST MODELS
# ============================================================

class ResearchRequest(BaseModel):
    query: str
    export_pdf: bool = False


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/")
def root():
    return {
        "status": "ok",
        "message": "Autonomous Research Agent API is running",
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
    }


# ============================================================
# BACKGROUND RESEARCH EXECUTION
# ============================================================

def execute_research(
    run_id: str,
    query: str,
    export_pdf: bool,
):

    try:

        result = run_research(
            query=query,
            export_pdf=export_pdf,
            run_id=run_id,
        )

        print(
            f"\n[RESEARCH COMPLETE] "
            f"run_id={run_id}"
        )

        print(
            f"[REPORT LENGTH] "
            f"{len(result.get('report', ''))}"
        )

        print(
            f"[SESSION ID] "
            f"{result.get('session_id', '')}"
        )

        complete_run(
            run_id,
            result,
        )

    except Exception as exc:

        print(
            f"\n[RESEARCH FAILED] "
            f"run_id={run_id}"
        )

        print(
            f"[ERROR] {exc}"
        )

        fail_run(
            run_id,
            str(exc),
        )

# ============================================================
# START RESEARCH
# ============================================================

@app.post("/research/start")
def start_research(request: ResearchRequest):

    query = request.query.strip()

    if not query:
        raise HTTPException(
            status_code=400,
            detail="Research query cannot be empty.",
        )

    run_id = create_run(
        query=query,
        export_pdf=request.export_pdf,
    )

    thread = Thread(
        target=execute_research,
        args=(
            run_id,
            query,
            request.export_pdf,
        ),
        daemon=True,
    )

    thread.start()

    return {
        "run_id": run_id,
        "status": "running",
        "message": "Research started.",
    }


# ============================================================
# LIVE RESEARCH STATUS
# ============================================================

@app.get("/research/status/{run_id}")
def research_status(run_id: str):

    run = get_run(run_id)

    if run is None:

        raise HTTPException(
            status_code=404,
            detail="Research run not found.",
        )

    return run


# ============================================================
# SYNCHRONOUS RESEARCH
# ============================================================

@app.post("/research")
def research(request: ResearchRequest):

    query = request.query.strip()

    if not query:
        raise HTTPException(
            status_code=400,
            detail="Research query cannot be empty.",
        )

    try:

        result = run_research(
            query=query,
            export_pdf=request.export_pdf,
        )

        return result

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )


# ============================================================
# MEMORY
# ============================================================

@app.get("/memory")
def get_memory():

    records = load_memory()

    return {
        "count": len(records),
        "sessions": records,
    }


@app.get("/memory/count")
def memory_count():

    return {
        "count": count_sessions(),
    }


@app.get("/memory/{session_id}")
def memory_session(session_id: str):

    session = get_session(session_id)

    if session is None:

        raise HTTPException(
            status_code=404,
            detail="Research session not found.",
        )

    return session


@app.delete("/memory/{session_id}")
def delete_memory_session(session_id: str):

    deleted = delete_session(session_id)

    if not deleted:

        raise HTTPException(
            status_code=404,
            detail="Research session not found.",
        )

    return {
        "success": True,
        "message": "Research session deleted.",
    }


@app.delete("/memory")
def delete_all_memory():

    clear_all()

    return {
        "success": True,
        "message": "All research memory deleted.",
    }


# ============================================================
# REPORTS
# ============================================================

@app.get("/reports")
def get_reports():

    sessions = load_memory()

    reports = []

    for session in sessions:

        markdown_path = session.get(
            "markdown_path",
            ""
        )

        pdf_path = session.get(
            "pdf_path",
            ""
        )

        markdown_exists = (
            bool(markdown_path)
            and Path(markdown_path).exists()
        )

        pdf_exists = (
            bool(pdf_path)
            and Path(pdf_path).exists()
        )

        reports.append(
            {
                "id": session.get("id"),
                "query": session.get("query"),
                "created_at": session.get("created_at"),
                "source_count": session.get(
                    "source_count",
                    0,
                ),
                "research_rounds": session.get(
                    "research_rounds",
                    1,
                ),
                "markdown_path": markdown_path,
                "pdf_path": pdf_path,
                "markdown_exists": markdown_exists,
                "pdf_exists": pdf_exists,
            }
        )

    return {
        "count": len(reports),
        "reports": reports,
    }


# ============================================================
# SAFE REPORT PATH
# ============================================================

def safe_report_path(filename: str) -> Path:

    filename = Path(filename).name

    path = EXPORT_DIR / filename

    try:
        path.resolve().relative_to(
            EXPORT_DIR.resolve()
        )
    except ValueError:

        raise HTTPException(
            status_code=400,
            detail="Invalid report filename.",
        )

    return path


# ============================================================
# READ MARKDOWN REPORT
# ============================================================

@app.get("/reports/{filename}")
def read_report(filename: str):

    path = safe_report_path(filename)

    if not path.exists():

        raise HTTPException(
            status_code=404,
            detail="Report not found.",
        )

    if path.suffix.lower() != ".md":

        raise HTTPException(
            status_code=400,
            detail="Only Markdown reports can be viewed.",
        )

    try:

        content = path.read_text(
            encoding="utf-8"
        )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )

    return PlainTextResponse(
        content,
        media_type="text/markdown",
    )


# ============================================================
# DOWNLOAD MARKDOWN
# ============================================================

@app.get("/reports/download")
def download_report(filename: str):

    path = safe_report_path(filename)

    if not path.exists():

        raise HTTPException(
            status_code=404,
            detail="Report not found.",
        )

    if path.suffix.lower() != ".md":

        raise HTTPException(
            status_code=400,
            detail="Only Markdown reports can be downloaded here.",
        )

    return FileResponse(
        path=str(path),
        filename=path.name,
        media_type="text/markdown",
    )


# ============================================================
# DOWNLOAD PDF
# ============================================================

@app.get("/reports/pdf")
def download_pdf(filename: str):

    path = safe_report_path(filename)

    if not path.exists():

        raise HTTPException(
            status_code=404,
            detail="PDF report not found.",
        )

    if path.suffix.lower() != ".pdf":

        raise HTTPException(
            status_code=400,
            detail="File is not a PDF.",
        )

    return FileResponse(
        path=str(path),
        filename=path.name,
        media_type="application/pdf",
    )


# ============================================================
# LEGACY PDF ENDPOINT
# ============================================================

@app.get("/research/pdf")
def legacy_download_pdf(filename: str):

    return download_pdf(filename)