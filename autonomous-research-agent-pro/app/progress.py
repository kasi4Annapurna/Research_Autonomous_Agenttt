"""
Live research execution progress tracking.
"""

from datetime import datetime, timezone
from threading import Lock
from uuid import uuid4


_runs = {}
_lock = Lock()


def create_run(
    query: str,
    export_pdf: bool = False,
) -> str:

    run_id = str(uuid4())

    with _lock:

        _runs[run_id] = {
            "run_id": run_id,
            "query": query,
            "export_pdf": export_pdf,

            "status": "running",

            "current_stage": "planning",
            "stage_number": 1,
            "total_stages": 8,

            "message": "Agent is starting the research workflow.",
            "detail": "",

            "research_round": 1,

            "sources_found": 0,

            "search_queries": [],

            "result": None,

            "error": None,

            "started_at": datetime.now(
                timezone.utc
            ).isoformat(),

            "completed_at": None,
        }

    return run_id


def update_run(
    run_id: str,
    status=None,
    stage=None,
    stage_number=None,
    message=None,
    detail=None,
    research_round=None,
    sources_found=None,
    search_queries=None,
    result=None,
    error=None,
):

    with _lock:

        if run_id not in _runs:
            return

        run = _runs[run_id]

        if status is not None:
            run["status"] = status

        if stage is not None:
            run["current_stage"] = stage

        if stage_number is not None:
            run["stage_number"] = stage_number

        if message is not None:
            run["message"] = message

        if detail is not None:
            run["detail"] = detail

        if research_round is not None:
            run["research_round"] = research_round

        if sources_found is not None:
            run["sources_found"] = sources_found

        if search_queries is not None:
            run["search_queries"] = search_queries

        if result is not None:
            run["result"] = result

        if error is not None:
            run["error"] = error

        if status in {"completed", "failed"}:

            run["completed_at"] = datetime.now(
                timezone.utc
            ).isoformat()


def get_run(run_id: str):

    with _lock:

        run = _runs.get(run_id)

        if run is None:
            return None

        # Return a copy so the API never exposes
        # the internal dictionary directly.
        return dict(run)


def complete_run(
    run_id: str,
    result,
):

    update_run(
        run_id=run_id,

        status="completed",

        stage="memory",

        stage_number=8,

        message="Research completed successfully.",

        detail="Final report is ready.",

        result=result,
    )


def fail_run(
    run_id: str,
    error: str,
):

    update_run(
        run_id=run_id,

        status="failed",

        message="Research failed.",

        detail=str(error),

        error=str(error),
    )