import { useEffect, useMemo, useState } from "react";
import "./styles.css";

const API_BASE = "/api";


// ============================================================
// HELPERS
// ============================================================

function formatDate(value) {
  if (!value) return "Unknown date";

  try {
    return new Date(value).toLocaleString();
  } catch {
    return value;
  }
}

function getFileName(path) {
  if (!path) return "";

  return path.split("\\").pop().split("/").pop();
}

function stageStatus(progress, stageNumber) {
  if (!progress) return "pending";

  if (progress.status === "completed") {
    return "completed";
  }

  if (progress.status === "failed") {
    if (stageNumber === progress.stage_number) {
      return "failed";
    }
  }

  if (stageNumber < progress.stage_number) {
    return "completed";
  }

  if (stageNumber === progress.stage_number) {
    return "active";
  }

  return "pending";
}


// ============================================================
// PIPELINE DATA
// ============================================================

const PIPELINE_STAGES = [
  {
    number: 1,
    key: "planning",
    title: "Planning",
    description: "Agent decomposes the research goal",
  },
  {
    number: 2,
    key: "research",
    title: "Web Research",
    description: "Searching multiple sources",
  },
  {
    number: 3,
    key: "filtering",
    title: "Source Filtering",
    description: "Removing duplicates and weak sources",
  },
  {
    number: 4,
    key: "evaluation",
    title: "Evidence Evaluation",
    description: "Checking evidence sufficiency",
  },
  {
    number: 5,
    key: "decision",
    title: "Agent Decision",
    description: "Deciding whether more research is needed",
  },
  {
    number: 6,
    key: "synthesis",
    title: "Synthesis",
    description: "Generating the final report",
  },
  {
    number: 7,
    key: "export",
    title: "Export",
    description: "Saving Markdown and PDF",
  },
  {
    number: 8,
    key: "memory",
    title: "Memory",
    description: "Saving the research session",
  },
];


// ============================================================
// APP
// ============================================================

export default function App() {
  const [page, setPage] = useState("research");

  return (
    <div className="app-shell">

      <Sidebar
        page={page}
        setPage={setPage}
      />

      <main className="main-content">

        {page === "research" && (
          <ResearchPage />
        )}

        {page === "reports" && (
          <ReportsPage />
        )}

        {page === "memory" && (
          <MemoryPage />
        )}

      </main>
    </div>
  );
}


// ============================================================
// SIDEBAR
// ============================================================

function Sidebar({ page, setPage }) {
  return (
    <aside className="sidebar">

      <div className="brand">

        <div className="brand-mark">
          AI
        </div>

        <div>
          <div className="brand-title">
            ResearchOS
          </div>

          <div className="brand-subtitle">
            Autonomous Intelligence
          </div>
        </div>

      </div>


      <div className="sidebar-section-title">
        WORKSPACE
      </div>


      <button
        className={`nav-item ${
          page === "research" ? "active" : ""
        }`}
        onClick={() => setPage("research")}
      >
        <span className="nav-icon">⌕</span>
        <span>Research Agent</span>
      </button>


      <button
        className={`nav-item ${
          page === "reports" ? "active" : ""
        }`}
        onClick={() => setPage("reports")}
      >
        <span className="nav-icon">▤</span>
        <span>Reports</span>
      </button>


      <button
        className={`nav-item ${
          page === "memory" ? "active" : ""
        }`}
        onClick={() => setPage("memory")}
      >
        <span className="nav-icon">◉</span>
        <span>Memory</span>
      </button>


      <div className="sidebar-bottom">

        <div className="agent-status">
          <span className="status-dot" />
          Agent Online
        </div>

        <div className="sidebar-version">
          Autonomous Research Agent v1.0
        </div>

      </div>

    </aside>
  );
}


// ============================================================
// RESEARCH PAGE
// ============================================================

function ResearchPage() {

  const [query, setQuery] = useState("");

  const [exportPdf, setExportPdf] = useState(true);

  const [running, setRunning] = useState(false);

  const [runId, setRunId] = useState(null);

  const [progress, setProgress] = useState(null);

  const [result, setResult] = useState(null);

  const [error, setError] = useState("");

  const [copied, setCopied] = useState(false);


  // ==========================================================
  // POLL RESEARCH STATUS
  // ==========================================================

  useEffect(() => {

    if (!runId) {
      return;
    }

    let cancelled = false;

    const pollStatus = async () => {

      try {

        const response = await fetch(
          `${API_BASE}/research/status/${runId}`
        );

        if (!response.ok) {

          const text = await response.text();

          throw new Error(
            `Status request failed (${response.status}): ${text}`
          );
        }

        const data = await response.json();

        if (cancelled) {
          return;
        }

        setProgress(data);


        // ====================================================
        // COMPLETED
        // ====================================================

        if (data.status === "completed") {

          setRunning(false);

          if (data.result) {
            setResult(data.result);
          }

          return;
        }


        // ====================================================
        // FAILED
        // ====================================================

        if (data.status === "failed") {

          setRunning(false);

          setError(
            data.error ||
            data.detail ||
            "Research failed."
          );

          return;
        }

      } catch (err) {

        if (cancelled) {
          return;
        }

        console.error(
          "Research status error:",
          err
        );

        setError(
          err.message ||
          "Unable to retrieve research status."
        );

      }
    };


    pollStatus();

    const timer = setInterval(
      pollStatus,
      1000
    );


    return () => {

      cancelled = true;

      clearInterval(timer);

    };

  }, [runId]);


  // ==========================================================
  // START RESEARCH
  // ==========================================================

  async function startResearch() {

    const trimmedQuery = query.trim();

    if (!trimmedQuery) {

      setError(
        "Please enter a research question."
      );

      return;
    }


    setError("");

    setResult(null);

    setProgress(null);

    setCopied(false);

    setRunning(true);

    setRunId(null);


    try {

      const response = await fetch(
        `${API_BASE}/research/start`,
        {
          method: "POST",

          headers: {
            "Content-Type": "application/json",
          },

          body: JSON.stringify({
            query: trimmedQuery,
            export_pdf: exportPdf,
          }),
        }
      );


      if (!response.ok) {

        const text = await response.text();

        throw new Error(
          `Failed to start research (${response.status}): ${text}`
        );
      }


      const data = await response.json();


      if (!data.run_id) {

        throw new Error(
          "Backend did not return a run_id."
        );
      }


      setRunId(data.run_id);

    } catch (err) {

      console.error(
        "Start research error:",
        err
      );

      setRunning(false);

      setError(
        err.message ||
        "Unable to start research."
      );
    }
  }


  // ==========================================================
  // ENTER KEY
  // ==========================================================

  function handleKeyDown(event) {

    if (
      event.key === "Enter" &&
      (event.ctrlKey || event.metaKey)
    ) {

      event.preventDefault();

      if (!running) {
        startResearch();
      }
    }
  }


  // ==========================================================
  // COPY REPORT
  // ==========================================================

  async function copyReport() {

    if (!result?.report) {
      return;
    }

    try {

      await navigator.clipboard.writeText(
        result.report
      );

      setCopied(true);

      setTimeout(
        () => setCopied(false),
        1500
      );

    } catch (err) {

      console.error(
        "Copy failed:",
        err
      );
    }
  }


  // ==========================================================
  // RESET
  // ==========================================================

  function newResearch() {

    setResult(null);

    setProgress(null);

    setError("");

    setRunId(null);

    setRunning(false);

    setCopied(false);

  }


  // ==========================================================
  // METRICS
  // ==========================================================

  const metrics = useMemo(() => {

    if (!result) {
      return [];
    }

    return [
      {
        label: "Sources",
        value:
          result.source_count ??
          result.sources?.length ??
          0,
      },
      {
        label: "Research Rounds",
        value:
          result.research_round ??
          1,
      },
      {
        label: "Queries",
        value:
          result.search_queries?.length ??
          0,
      },
      {
        label: "Status",
        value: "Complete",
      },
    ];

  }, [result]);


  // ==========================================================
  // REPORT VIEW
  // ==========================================================

  if (result) {

    return (
      <div className="page-container">

        <div className="topbar">

          <div>
            <div className="eyebrow">
              RESEARCH COMPLETE
            </div>

            <h1>
              Research Report
            </h1>

            <p className="page-description">
              Autonomous investigation completed and
              evidence synthesized.
            </p>
          </div>


          <button
            className="secondary-button"
            onClick={newResearch}
          >
            + New Research
          </button>

        </div>


        {/* METRICS */}

        <div className="metrics-grid">

          {metrics.map((metric) => (

            <div
              className="metric-card"
              key={metric.label}
            >

              <div className="metric-label">
                {metric.label}
              </div>

              <div className="metric-value">
                {metric.value}
              </div>

            </div>

          ))}

        </div>


        {/* REPORT */}

        <section className="result-card">

          <div className="result-header">

            <div>

              <div className="eyebrow">
                FINAL OUTPUT
              </div>

              <h2>
                {result.query}
              </h2>

            </div>


            <div className="result-actions">

              <button
                className="secondary-button"
                onClick={copyReport}
              >
                {copied ? "Copied ✓" : "Copy Report"}
              </button>


              {result.markdown_path && (

                <a
                  className="secondary-button"
                  href={`${API_BASE}/reports/download?filename=${encodeURIComponent(
                    getFileName(
                      result.markdown_path
                    )
                  )}`}
                  target="_blank"
                  rel="noreferrer"
                >
                  Markdown
                </a>

              )}


              {result.pdf_path && (

                <a
                  className="primary-button"
                  href={`${API_BASE}/reports/pdf?filename=${encodeURIComponent(
                    getFileName(
                      result.pdf_path
                    )
                  )}`}
                  target="_blank"
                  rel="noreferrer"
                >
                  Download PDF
                </a>

              )}

            </div>

          </div>


          <div className="report-body">

            {result.report ? (
              <ReportText
                text={result.report}
              />
            ) : (
              <div className="empty-state">
                The research completed, but no report text
                was returned by the backend.
              </div>
            )}

          </div>

        </section>


        {/* SEARCH QUERIES */}

        {result.search_queries?.length > 0 && (

          <section className="sources-section">

            <div className="section-heading">

              <div>
                <div className="eyebrow">
                  AGENT PLAN
                </div>

                <h2>
                  Research Queries
                </h2>
              </div>

            </div>


            <div className="query-list">

              {result.search_queries.map(
                (item, index) => (

                  <div
                    className="query-item"
                    key={`${item}-${index}`}
                  >

                    <span className="query-number">
                      {String(index + 1).padStart(2, "0")}
                    </span>

                    <span>
                      {item}
                    </span>

                  </div>

                )
              )}

            </div>

          </section>

        )}


        {/* SOURCES */}

        {result.sources?.length > 0 && (

          <section className="sources-section">

            <div className="section-heading">

              <div>
                <div className="eyebrow">
                  EVIDENCE
                </div>

                <h2>
                  Sources
                </h2>
              </div>

              <span className="section-count">
                {result.sources.length}
              </span>

            </div>


            <div className="sources-grid">

              {result.sources.map(
                (source, index) => (

                  <SourceCard
                    source={source}
                    index={index}
                    key={
                      source.url ||
                      `${source.title}-${index}`
                    }
                  />

                )
              )}

            </div>

          </section>

        )}

      </div>
    );
  }


  // ==========================================================
  // RESEARCH INPUT VIEW
  // ==========================================================

  return (
    <div className="page-container">

      <div className="topbar">

        <div>

          <div className="eyebrow">
            AUTONOMOUS RESEARCH
          </div>

          <h1>
            Research Agent
          </h1>

          <p className="page-description">
            Give the agent a high-level goal. It will
            plan, search, evaluate evidence, research again
            when necessary, and synthesize the result.
          </p>

        </div>

      </div>


      {/* INPUT CARD */}

      <section className="research-input-card">

        <div className="input-label">
          RESEARCH GOAL
        </div>


        <textarea
          value={query}
          onChange={(event) =>
            setQuery(event.target.value)
          }
          onKeyDown={handleKeyDown}
          disabled={running}
          placeholder="Example: What are the major applications, benefits, and risks of generative AI in software development?"
          className="research-textarea"
        />


        <div className="input-footer">

          <div className="input-hint">
            Press Ctrl + Enter to run
          </div>


          <div className="input-actions">

            <label className="toggle-wrapper">

              <input
                type="checkbox"
                checked={exportPdf}
                onChange={(event) =>
                  setExportPdf(
                    event.target.checked
                  )
                }
                disabled={running}
              />

              <span className="toggle">
                <span />
              </span>

              <span>
                Export PDF
              </span>

            </label>


            <button
              className="primary-button run-button"
              onClick={startResearch}
              disabled={running}
            >

              {running ? (
                <>
                  <span className="button-spinner" />
                  Agent Running...
                </>
              ) : (
                <>
                  Run Research →
                </>
              )}

            </button>

          </div>

        </div>

      </section>


      {/* ERROR */}

      {error && (

        <div className="error-card">

          <strong>
            Research error
          </strong>

          <div>
            {error}
          </div>

        </div>

      )}


      {/* LIVE PROGRESS */}

      {(running || progress) && (

        <ExecutionTimeline
          progress={progress}
          running={running}
        />

      )}


      {/* EXAMPLES */}

      {!running && !progress && (

        <section className="examples-section">

          <div className="section-heading">

            <div>

              <div className="eyebrow">
                TRY AN EXAMPLE
              </div>

              <h2>
                Research Goals
              </h2>

            </div>

          </div>


          <div className="examples-grid">

            {[
              "What are the major applications of generative AI in software development?",

              "How is AI changing cybersecurity and what are the major risks?",

              "What are the current trends in autonomous AI agents?",

              "How can companies use RAG systems effectively?",
            ].map((example) => (

              <button
                className="example-card"
                key={example}
                onClick={() =>
                  setQuery(example)
                }
              >

                <span className="example-arrow">
                  →
                </span>

                <span>
                  {example}
                </span>

              </button>

            ))}

          </div>

        </section>

      )}

    </div>
  );
}


// ============================================================
// EXECUTION TIMELINE
// ============================================================

function ExecutionTimeline({
  progress,
  running,
}) {

  const currentStage =
    progress?.stage_number || 1;


  return (
    <section className="execution-card">

      <div className="execution-header">

        <div>

          <div className="eyebrow">
            AGENT EXECUTION
          </div>

          <h2>
            {running
              ? "Autonomous workflow in progress"
              : progress?.status === "failed"
              ? "Research failed"
              : "Research completed"}
          </h2>

        </div>


        <div
          className={`execution-status ${
            progress?.status || "running"
          }`}
        >
          {progress?.status === "completed"
            ? "COMPLETE"
            : progress?.status === "failed"
            ? "FAILED"
            : "RUNNING"}
        </div>

      </div>


      <div className="current-progress">

        <div className="current-progress-title">
          {progress?.message ||
            "Agent is starting..."}
        </div>

        <div className="current-progress-detail">
          {progress?.detail ||
            "Initializing research workflow."}
        </div>

      </div>


      <div className="timeline">

        {PIPELINE_STAGES.map((stage) => {

          const status = stageStatus(
            progress,
            stage.number
          );


          return (
            <div
              className={`timeline-item ${status}`}
              key={stage.number}
            >

              <div className="timeline-marker">

                {status === "completed" && (
                  "✓"
                )}

                {status === "active" && (
                  <span className="timeline-spinner" />
                )}

                {status === "failed" && (
                  "!"
                )}

                {status === "pending" && (
                  stage.number
                )}

              </div>


              <div className="timeline-content">

                <div className="timeline-title">

                  <span>
                    {String(stage.number).padStart(
                      2,
                      "0"
                    )}{" "}
                    {stage.title}
                  </span>

                  {status === "active" && (
                    <span className="active-label">
                      ACTIVE
                    </span>
                  )}

                </div>


                <div className="timeline-description">
                  {stage.description}
                </div>


                {status === "active" &&
                  progress?.stage_number ===
                    stage.number && (

                    <div className="timeline-detail">

                      {progress.detail ||
                        progress.message}

                    </div>

                  )}

              </div>

            </div>
          );

        })}

      </div>


      <div className="execution-footer">

        <div>
          Research round:{" "}
          <strong>
            {progress?.research_round || 1}
          </strong>
        </div>

        <div>
          Sources discovered:{" "}
          <strong>
            {progress?.sources_found || 0}
          </strong>
        </div>

        {progress?.search_queries?.length > 0 && (

          <div>
            Queries:{" "}
            <strong>
              {progress.search_queries.length}
            </strong>
          </div>

        )}

      </div>

    </section>
  );
}


// ============================================================
// REPORT TEXT
// ============================================================

function ReportText({ text }) {

  const lines = String(text).split("\n");

  return (
    <div className="formatted-report">

      {lines.map((line, index) => {

        const trimmed = line.trim();


        if (!trimmed) {
          return (
            <div
              className="report-spacer"
              key={index}
            />
          );
        }


        if (trimmed.startsWith("### ")) {

          return (
            <h4 key={index}>
              {trimmed.replace(
                "### ",
                ""
              )}
            </h4>
          );
        }


        if (trimmed.startsWith("## ")) {

          return (
            <h3 key={index}>
              {trimmed.replace(
                "## ",
                ""
              )}
            </h3>
          );
        }


        if (trimmed.startsWith("# ")) {

          return (
            <h2 key={index}>
              {trimmed.replace(
                "# ",
                ""
              )}
            </h2>
          );
        }


        if (
          trimmed.startsWith("- ") ||
          trimmed.startsWith("* ")
        ) {

          return (
            <div
              className="report-bullet"
              key={index}
            >
              <span>•</span>
              <span>
                {trimmed.substring(2)}
              </span>
            </div>
          );
        }


        if (/^\d+\.\s/.test(trimmed)) {

          return (
            <div
              className="report-numbered"
              key={index}
            >
              {trimmed}
            </div>
          );
        }


        return (
          <p key={index}>
            {trimmed}
          </p>
        );

      })}

    </div>
  );
}


// ============================================================
// SOURCE CARD
// ============================================================

function SourceCard({
  source,
  index,
}) {

  const title =
    source.title ||
    source.name ||
    `Source ${index + 1}`;

  const url =
    source.url ||
    source.link ||
    "";

  const snippet =
    source.snippet ||
    source.content ||
    source.text ||
    "";


  return (
    <div className="source-card">

      <div className="source-number">
        {String(index + 1).padStart(2, "0")}
      </div>


      <div className="source-content">

        <h3>
          {title}
        </h3>


        {snippet && (

          <p>
            {snippet}
          </p>

        )}


        {url && (

          <a
            href={url}
            target="_blank"
            rel="noreferrer"
            className="source-link"
          >
            Open source →
          </a>

        )}

      </div>

    </div>
  );
}


// ============================================================
// REPORTS PAGE
// ============================================================

function ReportsPage() {

  const [reports, setReports] = useState([]);

  const [loading, setLoading] = useState(true);

  const [error, setError] = useState("");


  async function loadReports() {

    setLoading(true);

    setError("");

    try {

      const response = await fetch(
        `${API_BASE}/reports`
      );

      if (!response.ok) {

        throw new Error(
          `Failed to load reports (${response.status})`
        );
      }

      const data = await response.json();

      setReports(
        data.reports || []
      );

    } catch (err) {

      console.error(
        "Reports error:",
        err
      );

      setError(
        err.message ||
        "Unable to load reports."
      );

    } finally {

      setLoading(false);

    }
  }


  useEffect(() => {

    loadReports();

  }, []);


  return (
    <div className="page-container">

      <div className="topbar">

        <div>

          <div className="eyebrow">
            ARCHIVE
          </div>

          <h1>
            Reports
          </h1>

          <p className="page-description">
            Every completed research investigation
            saved by the agent.
          </p>

        </div>


        <button
          className="secondary-button"
          onClick={loadReports}
        >
          Refresh
        </button>

      </div>


      {loading && (
        <div className="loading-card">
          Loading reports...
        </div>
      )}


      {error && (
        <div className="error-card">
          {error}
        </div>
      )}


      {!loading &&
        !error &&
        reports.length === 0 && (

          <div className="empty-card">

            <div className="empty-icon">
              ▤
            </div>

            <h2>
              No reports yet
            </h2>

            <p>
              Run your first research task and the
              generated report will appear here.
            </p>

          </div>

        )}


      <div className="reports-list">

        {reports.map((report) => {

          const markdownFile =
            getFileName(
              report.markdown_path
            );

          const pdfFile =
            getFileName(
              report.pdf_path
            );


          return (
            <div
              className="report-list-card"
              key={
                report.id ||
                report.markdown_path ||
                report.query
              }
            >

              <div className="report-list-main">

                <div className="report-list-icon">
                  R
                </div>

                <div>

                  <h2>
                    {report.query}
                  </h2>

                  <div className="report-meta">

                    <span>
                      {formatDate(
                        report.created_at
                      )}
                    </span>

                    <span>
                      {report.source_count || 0}
                      {" "}sources
                    </span>

                    <span>
                      {report.research_rounds || 1}
                      {" "}rounds
                    </span>

                  </div>

                </div>

              </div>


              <div className="report-list-actions">

                {report.markdown_exists &&
                  markdownFile && (

                    <a
                      className="secondary-button"
                      href={`${API_BASE}/reports/${encodeURIComponent(
                        markdownFile
                      )}`}
                      target="_blank"
                      rel="noreferrer"
                    >
                      View
                    </a>

                  )}


                {report.markdown_exists &&
                  markdownFile && (

                    <a
                      className="secondary-button"
                      href={`${API_BASE}/reports/download?filename=${encodeURIComponent(
                        markdownFile
                      )}`}
                    >
                      MD
                    </a>

                  )}


                {report.pdf_exists &&
                  pdfFile && (

                    <a
                      className="primary-button"
                      href={`${API_BASE}/reports/pdf?filename=${encodeURIComponent(
                        pdfFile
                      )}`}
                      target="_blank"
                      rel="noreferrer"
                    >
                      PDF
                    </a>

                  )}

              </div>

            </div>
          );

        })}

      </div>

    </div>
  );
}


// ============================================================
// MEMORY PAGE
// ============================================================

function MemoryPage() {

  const [sessions, setSessions] = useState([]);

  const [loading, setLoading] = useState(true);

  const [error, setError] = useState("");

  const [selected, setSelected] = useState(null);


  async function loadMemory() {

    setLoading(true);

    setError("");

    try {

      const response = await fetch(
        `${API_BASE}/memory`
      );

      if (!response.ok) {

        throw new Error(
          `Failed to load memory (${response.status})`
        );
      }

      const data = await response.json();

      setSessions(
        data.sessions || []
      );

    } catch (err) {

      console.error(
        "Memory error:",
        err
      );

      setError(
        err.message ||
        "Unable to load memory."
      );

    } finally {

      setLoading(false);

    }
  }


  useEffect(() => {

    loadMemory();

  }, []);


  async function deleteSession(id) {

    if (!id) return;

    const confirmed =
      window.confirm(
        "Delete this research session?"
      );

    if (!confirmed) {
      return;
    }


    try {

      const response = await fetch(
        `${API_BASE}/memory/${id}`,
        {
          method: "DELETE",
        }
      );


      if (!response.ok) {

        throw new Error(
          "Unable to delete session."
        );
      }


      if (
        selected &&
        selected.id === id
      ) {

        setSelected(null);

      }


      await loadMemory();

    } catch (err) {

      setError(
        err.message ||
        "Unable to delete session."
      );

    }
  }


  return (
    <div className="page-container">

      <div className="topbar">

        <div>

          <div className="eyebrow">
            PERSISTENT MEMORY
          </div>

          <h1>
            Research Memory
          </h1>

          <p className="page-description">
            Completed research sessions stored in
            SQLite.
          </p>

        </div>


        <button
          className="secondary-button"
          onClick={loadMemory}
        >
          Refresh
        </button>

      </div>


      {loading && (
        <div className="loading-card">
          Loading memory...
        </div>
      )}


      {error && (
        <div className="error-card">
          {error}
        </div>
      )}


      {!loading &&
        !error &&
        sessions.length === 0 && (

          <div className="empty-card">

            <div className="empty-icon">
              ◉
            </div>

            <h2>
              Memory is empty
            </h2>

            <p>
              Completed research sessions will be
              persisted here.
            </p>

          </div>

        )}


      <div className="memory-list">

        {sessions.map((session) => (

          <div
            className="memory-card"
            key={session.id}
          >

            <div className="memory-main">

              <div className="memory-icon">
                AI
              </div>

              <div>

                <h2>
                  {session.query}
                </h2>

                <div className="memory-meta">

                  <span>
                    {formatDate(
                      session.created_at
                    )}
                  </span>

                  <span>
                    {session.source_count || 0}
                    {" "}sources
                  </span>

                  <span>
                    {session.research_rounds || 1}
                    {" "}rounds
                  </span>

                </div>

              </div>

            </div>


            <div className="memory-actions">

              <button
                className="secondary-button"
                onClick={() =>
                  setSelected(session)
                }
              >
                View
              </button>


              <button
                className="danger-button"
                onClick={() =>
                  deleteSession(session.id)
                }
              >
                Delete
              </button>

            </div>

          </div>

        ))}

      </div>


      {/* MEMORY DETAIL */}

      {selected && (

        <div className="memory-detail-card">

          <div className="result-header">

            <div>

              <div className="eyebrow">
                STORED SESSION
              </div>

              <h2>
                {selected.query}
              </h2>

            </div>


            <button
              className="secondary-button"
              onClick={() =>
                setSelected(null)
              }
            >
              Close
            </button>

          </div>


          <div className="report-body">

            <ReportText
              text={
                selected.report ||
                "No report content stored."
              }
            />

          </div>

        </div>

      )}

    </div>
  );
}