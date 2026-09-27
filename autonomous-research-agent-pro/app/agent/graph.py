import json
import os
from typing import Any, Dict, List, TypedDict

from langgraph.graph import StateGraph, START, END
from langchain_groq import ChatGroq

from config import settings
from app.tools.search import parallel_search
from app.tools.export import export_report
from app.memory.store import save as save_memory
from app.progress import update_run


# ============================================================
# CONSTANTS
# ============================================================

MAX_TOTAL_CHARS = 14000
MAX_SOURCE_CHARS = 1800
MAX_RESEARCH_ROUNDS = 2


# ============================================================
# STATE
# ============================================================

class ResearchState(TypedDict, total=False):
    query: str

    search_queries: List[str]

    raw_sources: List[Dict[str, Any]]

    sources: List[Dict[str, Any]]

    evidence_assessment: Dict[str, Any]

    research_round: int
    max_research_rounds: int

    report: Any
    markdown: str

    markdown_path: str
    pdf_path: str

    export_pdf: bool

    session_id: str
    run_id: str


# ============================================================
# LLM
# ============================================================

llm = ChatGroq(
    model=settings.groq_model,
    api_key=settings.groq_api_key,
    temperature=0.2,
)


# ============================================================
# HELPERS
# ============================================================

def progress(state: ResearchState, **kwargs):
    """
    Update frontend progress if this run has a run_id.
    """
    run_id = state.get("run_id")

    if run_id:
        update_run(run_id, **kwargs)


def safe_json_response(response) -> Dict[str, Any]:
    """
    Safely convert an LLM response into a dictionary.
    """

    content = getattr(response, "content", response)

    if isinstance(content, list):
        parts = []

        for item in content:
            if isinstance(item, dict):
                parts.append(str(item.get("text", item)))
            else:
                parts.append(str(item))

        content = "\n".join(parts)

    if isinstance(content, dict):
        return content

    content = str(content).strip()

    # Remove markdown code fences if the model returned them.
    if content.startswith("```"):
        content = content.replace("```json", "", 1)
        content = content.replace("```", "")
        content = content.strip()

    try:
        return json.loads(content)
    except Exception:
        return {
            "text": content
        }


def report_to_string(report: Any) -> str:
    """
    IMPORTANT:
    Exporters need a string.

    The LLM may return a dictionary/list, so this function
    guarantees that the final report is always a string.
    """

    if report is None:
        return ""

    if isinstance(report, str):
        return report

    if isinstance(report, dict):
        # Preferred structured report conversion.
        sections = []

        preferred_order = [
            "title",
            "executive_summary",
            "summary",
            "key_findings",
            "findings",
            "analysis",
            "insights",
            "recommendations",
            "limitations",
            "sources",
            "references",
        ]

        used = set()

        for key in preferred_order:
            if key not in report:
                continue

            used.add(key)

            value = report[key]

            title = key.replace("_", " ").title()

            sections.append(f"## {title}")

            if isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        sections.append(
                            "- " + json.dumps(
                                item,
                                ensure_ascii=False
                            )
                        )
                    else:
                        sections.append(f"- {item}")

            elif isinstance(value, dict):
                sections.append(
                    json.dumps(
                        value,
                        indent=2,
                        ensure_ascii=False
                    )
                )

            else:
                sections.append(str(value))

        # Add any fields we didn't explicitly recognize.
        for key, value in report.items():

            if key in used:
                continue

            title = str(key).replace("_", " ").title()

            sections.append(f"## {title}")

            if isinstance(value, (dict, list)):
                sections.append(
                    json.dumps(
                        value,
                        indent=2,
                        ensure_ascii=False
                    )
                )
            else:
                sections.append(str(value))

        return "\n\n".join(sections).strip()

    if isinstance(report, list):
        lines = []

        for item in report:
            if isinstance(item, dict):
                lines.append(
                    json.dumps(
                        item,
                        ensure_ascii=False
                    )
                )
            else:
                lines.append(str(item))

        return "\n".join(lines)

    return str(report)


def clean_source(source: Dict[str, Any]) -> Dict[str, Any]:
    """
    Keep only useful source fields and limit text size.
    """

    if not isinstance(source, dict):
        return {
            "title": "",
            "url": "",
            "snippet": str(source)[:MAX_SOURCE_CHARS],
        }

    return {
        "title": str(
            source.get("title")
            or source.get("name")
            or ""
        )[:500],

        "url": str(
            source.get("url")
            or source.get("link")
            or ""
        )[:1000],

        "snippet": str(
            source.get("snippet")
            or source.get("content")
            or source.get("text")
            or ""
        )[:MAX_SOURCE_CHARS],
    }


def build_source_context(
    sources: List[Dict[str, Any]]
) -> str:

    chunks = []
    total_chars = 0

    for index, source in enumerate(sources, start=1):

        cleaned = clean_source(source)

        chunk = (
            f"SOURCE {index}\n"
            f"Title: {cleaned['title']}\n"
            f"URL: {cleaned['url']}\n"
            f"Content: {cleaned['snippet']}\n"
        )

        if total_chars + len(chunk) > MAX_TOTAL_CHARS:
            break

        chunks.append(chunk)
        total_chars += len(chunk)

    return "\n\n".join(chunks)


# ============================================================
# NODE 1 — PLANNING
# ============================================================

def plan_research(state: ResearchState) -> ResearchState:

    query = state["query"]

    progress(
        state,
        stage="planning",
        stage_number=1,
        message="Agent is decomposing the research goal.",
        detail="Generating multiple research queries.",
    )

    prompt = f"""
You are an autonomous research planning agent.

User research goal:
{query}

Break this goal into 4 to 6 focused web-search queries.

The queries should cover different aspects of the goal.

Return ONLY valid JSON:

{{
  "queries": [
    "query 1",
    "query 2",
    "query 3",
    "query 4"
  ]
}}
"""

    try:
        response = llm.invoke(
            prompt,
            response_format={"type": "json_object"},
        )

        data = safe_json_response(response)

        queries = data.get("queries", [])

        if not isinstance(queries, list):
            queries = []

        queries = [
            str(q).strip()
            for q in queries
            if str(q).strip()
        ]

    except Exception:
        queries = []

    if not queries:
        queries = [
            query,
            f"{query} latest research",
            f"{query} benefits risks",
            f"{query} expert analysis",
        ]

    queries = queries[:6]

    progress(
        state,
        search_queries=queries,
        detail=f"Generated {len(queries)} research queries.",
    )

    return {
        **state,
        "search_queries": queries,
        "research_round": 1,
        "max_research_rounds": MAX_RESEARCH_ROUNDS,
    }


# ============================================================
# NODE 2 — WEB RESEARCH
# ============================================================

def gather_research(state: ResearchState) -> ResearchState:

    research_round = state.get("research_round", 1)

    progress(
        state,
        stage="research",
        stage_number=2,
        research_round=research_round,
        message="Searching multiple web sources.",
        detail=f"Research round {research_round}.",
    )

    queries = state.get("search_queries", [])

    try:
        results = parallel_search(queries)
    except Exception as exc:
        results = []

        progress(
            state,
            detail=f"Search returned an error: {str(exc)[:200]}",
        )

    if not isinstance(results, list):
        results = []

    existing = state.get("raw_sources", [])

    combined = existing + results

    progress(
        state,
        sources_found=len(combined),
        detail=f"{len(results)} sources collected this round.",
    )

    return {
        **state,
        "raw_sources": combined,
    }


# ============================================================
# NODE 3 — CLEAN / FILTER
# ============================================================

def clean_and_filter(state: ResearchState) -> ResearchState:

    progress(
        state,
        stage="filtering",
        stage_number=3,
        message="Filtering research sources.",
        detail="Removing duplicates and unusable sources.",
    )

    raw_sources = state.get("raw_sources", [])

    cleaned = []

    seen_urls = set()

    for source in raw_sources:

        item = clean_source(source)

        url = item["url"].strip()

        if url and url in seen_urls:
            continue

        if url:
            seen_urls.add(url)

        # Keep sources that have at least a title, URL, or content.
        if (
            item["title"]
            or item["url"]
            or item["snippet"]
        ):
            cleaned.append(item)

    progress(
        state,
        sources_found=len(cleaned),
        detail=f"{len(cleaned)} usable sources remain.",
    )

    return {
        **state,
        "sources": cleaned,
    }


# ============================================================
# NODE 4 — EVIDENCE EVALUATION
# ============================================================

def evaluate_evidence(state: ResearchState) -> ResearchState:

    sources = state.get("sources", [])

    progress(
        state,
        stage="evaluation",
        stage_number=4,
        message="Evaluating evidence sufficiency.",
        detail="Checking coverage, quality, and research gaps.",
    )

    context = build_source_context(sources)

    prompt = f"""
You are an evidence evaluation agent.

Research goal:
{state["query"]}

Collected sources:
{context}

Evaluate whether the evidence is sufficient to answer the research goal.

Return ONLY JSON:

{{
  "sufficient": true,
  "confidence": "high",
  "reason": "short explanation",
  "missing_topics": [
    "topic 1",
    "topic 2"
  ]
}}

Set sufficient=false if important aspects of the research goal
are not adequately supported.
"""

    try:
        response = llm.invoke(
            prompt,
            response_format={"type": "json_object"},
        )

        assessment = safe_json_response(response)

    except Exception as exc:

        assessment = {
            "sufficient": len(sources) >= 5,
            "confidence": "medium",
            "reason": str(exc)[:200],
            "missing_topics": [],
        }

    if not isinstance(assessment, dict):
        assessment = {
            "sufficient": len(sources) >= 5,
            "confidence": "medium",
            "reason": "Unable to parse evidence assessment.",
            "missing_topics": [],
        }

    progress(
        state,
        detail=(
            "Evidence appears sufficient."
            if assessment.get("sufficient")
            else "Evidence appears insufficient."
        ),
    )

    return {
        **state,
        "evidence_assessment": assessment,
    }


# ============================================================
# NODE 5 — DECISION / RESEARCH AGAIN
# ============================================================

def research_decision(state: ResearchState) -> str:

    assessment = state.get(
        "evidence_assessment",
        {}
    )

    sufficient = bool(
        assessment.get("sufficient", False)
    )

    research_round = state.get(
        "research_round",
        1
    )

    max_rounds = state.get(
        "max_research_rounds",
        MAX_RESEARCH_ROUNDS
    )

    if sufficient:

        progress(
            state,
            stage="decision",
            stage_number=5,
            message="Evidence is sufficient.",
            detail="Agent decided to proceed to synthesis.",
        )

        return "synthesize"

    if research_round >= max_rounds:

        progress(
            state,
            stage="decision",
            stage_number=5,
            message="Research limit reached.",
            detail="Proceeding with the available evidence.",
        )

        return "synthesize"

    progress(
        state,
        stage="decision",
        stage_number=5,
        message="Evidence is insufficient.",
        detail="Agent decided to perform another research round.",
    )

    return "research_again"


# ============================================================
# NODE 6 — RESEARCH AGAIN
# ============================================================

def research_again(state: ResearchState) -> ResearchState:

    current_round = state.get(
        "research_round",
        1
    )

    next_round = current_round + 1

    assessment = state.get(
        "evidence_assessment",
        {}
    )

    missing_topics = assessment.get(
        "missing_topics",
        []
    )

    if not isinstance(missing_topics, list):
        missing_topics = []

    missing_topics = [
        str(topic).strip()
        for topic in missing_topics
        if str(topic).strip()
    ]

    if not missing_topics:
        missing_topics = [
            f"{state['query']} additional evidence",
            f"{state['query']} expert analysis",
            f"{state['query']} risks limitations",
        ]

    new_queries = [
        f"{state['query']} {topic}"
        for topic in missing_topics[:4]
    ]

    progress(
        state,
        stage="research_again",
        stage_number=5,
        research_round=next_round,
        message="Autonomous research loop triggered.",
        detail=(
            f"Agent generated {len(new_queries)} "
            "additional research queries."
        ),
        search_queries=new_queries,
    )

    return {
        **state,
        "research_round": next_round,
        "search_queries": new_queries,
    }


# ============================================================
# NODE 7 — SYNTHESIS
# ============================================================

def synthesize_report(state: ResearchState) -> ResearchState:

    progress(
        state,
        stage="synthesis",
        stage_number=6,
        message="Synthesizing the final research report.",
        detail="Combining evidence into a structured answer.",
    )

    sources = state.get("sources", [])

    context = build_source_context(sources)

    prompt = f"""
You are an autonomous research synthesis agent.

Research goal:
{state["query"]}

Evidence:
{context}

Create a structured research report.

The report must include:

1. Title
2. Executive summary
3. Key findings
4. Detailed analysis
5. Practical insights
6. Limitations / uncertainty
7. Sources

Important:
- Do not invent facts.
- Clearly distinguish evidence from interpretation.
- Use the supplied sources.
- Include source URLs where appropriate.

Return ONLY valid JSON:

{{
  "title": "...",
  "executive_summary": "...",
  "key_findings": [
    "...",
    "..."
  ],
  "analysis": "...",
  "insights": [
    "...",
    "..."
  ],
  "limitations": [
    "...",
    "..."
  ],
  "sources": [
    {{
      "title": "...",
      "url": "..."
    }}
  ]
}}
"""

    try:

        response = llm.invoke(
            prompt,
            response_format={"type": "json_object"},
        )

        report = safe_json_response(response)

    except Exception as exc:

        report = {
            "title": state["query"],
            "executive_summary": (
                "The research agent collected "
                f"{len(sources)} sources."
            ),
            "key_findings": [],
            "analysis": (
                "Synthesis could not be completed automatically: "
                + str(exc)
            ),
            "insights": [],
            "limitations": [
                "Automated synthesis encountered an error."
            ],
            "sources": [
                {
                    "title": source.get("title", ""),
                    "url": source.get("url", ""),
                }
                for source in sources
            ],
        }

    # ========================================================
    # CRITICAL FIX
    # ========================================================
    # Convert dictionary/list response into a STRING before
    # sending it to the exporter.
    # ========================================================

    report_string = report_to_string(report)

    return {
        **state,
        "report": report,
        "markdown": report_string,
    }


# ============================================================
# NODE 8 — EXPORT + MEMORY
# ============================================================

def finalize_report(state: ResearchState) -> ResearchState:

    progress(
        state,
        stage="export",
        stage_number=7,
        message="Exporting the research report.",
        detail="Creating Markdown and optional PDF.",
    )

    query = state["query"]

    # ALWAYS use the string version.
    report_string = report_to_string(
        state.get("report")
        or state.get("markdown")
        or ""
    )

    export_pdf = bool(
        state.get("export_pdf", False)
    )

    markdown_path = ""
    pdf_path = ""

    try:

        export_result = export_report(
            query=query,
            report=report_string,
            generate_pdf=export_pdf,
        )

        if isinstance(export_result, dict):

            markdown_path = str(
                export_result.get(
                    "markdown_path",
                    ""
                )
            )

            pdf_path = str(
                export_result.get(
                    "pdf_path",
                    ""
                )
            )

        elif isinstance(export_result, tuple):

            if len(export_result) >= 1:
                markdown_path = str(
                    export_result[0] or ""
                )

            if len(export_result) >= 2:
                pdf_path = str(
                    export_result[1] or ""
                )

        elif isinstance(export_result, str):

            markdown_path = export_result

    except Exception as exc:

        progress(
            state,
            detail=f"Export warning: {str(exc)[:200]}",
        )

    # ========================================================
    # SAVE TO SQLITE
    # ========================================================

    progress(
        state,
        stage="memory",
        stage_number=8,
        message="Saving research session to SQLite.",
        detail="Persisting report and research metadata.",
    )

    try:

        session_id = save_memory(
            query=query,
            report=report_string,
            search_queries=state.get(
                "search_queries",
                []
            ),
            source_count=len(
                state.get("sources", [])
            ),
            research_rounds=state.get(
                "research_round",
                1
            ),
            markdown_path=markdown_path,
            pdf_path=pdf_path,
        )

    except Exception as exc:

        session_id = ""

        progress(
            state,
            detail=f"Memory warning: {str(exc)[:200]}",
        )

    final_state = {
        **state,
        "report": report_string,
        "markdown": report_string,
        "markdown_path": markdown_path,
        "pdf_path": pdf_path,
        "session_id": session_id,
    }

    progress(
        final_state,
        stage="memory",
        stage_number=8,
        message="Research completed successfully.",
        detail="Report saved to SQLite memory.",
    )

    return final_state


# ============================================================
# GRAPH
# ============================================================

def build_graph():

    graph = StateGraph(ResearchState)

    graph.add_node(
        "plan",
        plan_research
    )

    graph.add_node(
        "gather",
        gather_research
    )

    graph.add_node(
        "clean",
        clean_and_filter
    )

    graph.add_node(
        "analyze",
        evaluate_evidence
    )

    graph.add_node(
        "research_again",
        research_again
    )

    graph.add_node(
        "synthesize",
        synthesize_report
    )

    graph.add_node(
        "finalize",
        finalize_report
    )

    # START → PLAN
    graph.add_edge(
        START,
        "plan"
    )

    # PLAN → RESEARCH
    graph.add_edge(
        "plan",
        "gather"
    )

    # RESEARCH → FILTER
    graph.add_edge(
        "gather",
        "clean"
    )

    # FILTER → EVALUATION
    graph.add_edge(
        "clean",
        "analyze"
    )

    # EVALUATION → DECISION
    graph.add_conditional_edges(
        "analyze",
        research_decision,
        {
            "research_again": "research_again",
            "synthesize": "synthesize",
        },
    )

    # RESEARCH AGAIN → RESEARCH
    graph.add_edge(
        "research_again",
        "gather"
    )

    # SYNTHESIS → EXPORT/MEMORY
    graph.add_edge(
        "synthesize",
        "finalize"
    )

    # FINALIZE → END
    graph.add_edge(
        "finalize",
        END
    )

    return graph.compile()


# ============================================================
# COMPILED GRAPH
# ============================================================

research_graph = build_graph()


# ============================================================
# PUBLIC RUN FUNCTION
# ============================================================

def run_research(
    query: str,
    export_pdf: bool = False,
    run_id: str | None = None,
):

    query = str(query).strip()

    if not query:
        raise ValueError(
            "Research query cannot be empty."
        )

    initial_state: ResearchState = {
        "query": query,
        "search_queries": [],
        "raw_sources": [],
        "sources": [],
        "evidence_assessment": {},
        "research_round": 1,
        "max_research_rounds": MAX_RESEARCH_ROUNDS,
        "report": "",
        "markdown": "",
        "markdown_path": "",
        "pdf_path": "",
        "export_pdf": export_pdf,
        "session_id": "",
        "run_id": run_id or "",
    }

    result = research_graph.invoke(
        initial_state
    )

    # Ensure report is ALWAYS a string.
    report_string = report_to_string(
        result.get("report")
        or result.get("markdown")
        or ""
    )

    return {
        "query": query,

        "search_queries": result.get(
            "search_queries",
            []
        ),

        "sources": result.get(
            "sources",
            []
        ),

        "source_count": len(
            result.get("sources", [])
        ),

        "research_round": result.get(
            "research_round",
            1
        ),

        "evidence_assessment": result.get(
            "evidence_assessment",
            {}
        ),

        "report": report_string,

        "markdown": report_string,

        "markdown_path": result.get(
            "markdown_path",
            ""
        ),

        "pdf_path": result.get(
            "pdf_path",
            ""
        ),

        "session_id": result.get(
            "session_id",
            ""
        ),

        "run_id": run_id or "",
    }