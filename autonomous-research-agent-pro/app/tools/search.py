
import asyncio
from urllib.parse import urlsplit, urlunsplit

import httpx
from bs4 import BeautifulSoup
from tavily import TavilyClient

from config import settings


# ============================================================
# 1. TAVILY CLIENT
# ============================================================

client = TavilyClient(
    api_key=settings.tavily_api_key
)


# ============================================================
# 2. URL NORMALIZATION
# ============================================================

def normalize_url(url: str) -> str:
    """
    Convert a URL into a consistent format.

    Example:
        https://Example.com/article/
    becomes:
        https://example.com/article
    """

    if not url:
        return ""

    parts = urlsplit(url.strip())

    return urlunsplit(
        (
            parts.scheme.lower(),
            parts.netloc.lower(),
            parts.path.rstrip("/"),
            "",
            "",
        )
    )


# ============================================================
# 3. TAVILY SEARCH
# ============================================================

def search(query: str) -> list[dict]:
    """
    Search the web using Tavily.

    Tavily is our external information-retrieval tool.
    Groq is the reasoning/LLM layer.
    """

    try:
        response = client.search(
            query=query,
            search_depth="advanced",
            max_results=settings.max_results_per_query,
            include_answer=False,
        )

        return response.get("results", [])

    except Exception as exc:
        print(f"[TAVILY ERROR] Query={query!r} Error={exc}")
        return []


# ============================================================
# 4. WEBPAGE FETCHING
# ============================================================

async def fetch(
    url: str,
    http_client: httpx.AsyncClient,
) -> str:
    """
    Download one webpage asynchronously and extract readable text.
    """

    if not url:
        return ""

    try:
        response = await http_client.get(url)

        response.raise_for_status()

        soup = BeautifulSoup(
            response.text,
            "html.parser",
        )

        # Remove elements that usually do not contain
        # useful research information.
        for tag in soup(
            [
                "script",
                "style",
                "noscript",
                "svg",
                "nav",
                "footer",
                "header",
                "aside",
                "form",
            ]
        ):
            tag.decompose()

        text = " ".join(
            soup.stripped_strings
        )

        return text[: settings.max_content_chars]

    except Exception as exc:
        print(f"[FETCH ERROR] URL={url!r} Error={exc}")
        return ""


# ============================================================
# 5. GATHER ONE QUERY
# ============================================================

async def gather_one(
    query: str,
    http_client: httpx.AsyncClient,
) -> list[dict]:
    """
    Execute one Tavily query and fetch all returned
    webpages concurrently.
    """

    # TavilyClient.search() is synchronous.
    #
    # asyncio.to_thread() moves the blocking Tavily call
    # into a worker thread so our async event loop can
    # continue running other work.
    results = await asyncio.to_thread(
        search,
        query,
    )

    if not results:
        return []

    # Create one asynchronous task per webpage.
    tasks = [
        fetch(
            result.get("url", ""),
            http_client,
        )
        for result in results
        if result.get("url")
    ]

    # Download all webpages concurrently.
    pages = await asyncio.gather(
        *tasks,
        return_exceptions=True,
    )

    output = []

    page_index = 0

    for result in results:

        url = result.get("url", "")

        if not url:
            continue

        page = pages[page_index]
        page_index += 1

        if isinstance(page, Exception):
            content = ""
        else:
            content = page

        # If direct webpage extraction failed,
        # use Tavily's own result content.
        if not content:
            content = result.get("content", "")

        output.append(
            {
                "title": result.get("title", ""),
                "url": url,
                "query": query,
                "content": content,
                "score": float(
                    result.get("score", 0.0) or 0.0
                ),
            }
        )

    return output


# ============================================================
# 6. PARALLEL RESEARCH
# ============================================================

async def gather_parallel(
    queries: list[str],
) -> list[dict]:
    """
    Execute multiple research queries concurrently.

    Example:

        Query 1 ─┐
        Query 2 ─┼──> concurrent execution
        Query 3 ─┤
        Query 4 ─┘
    """

    if not queries:
        return []

    timeout = httpx.Timeout(
        settings.request_timeout_seconds
    )

    limits = httpx.Limits(
        max_connections=20,
        max_keepalive_connections=10,
    )

    headers = {
        "User-Agent": "AutonomousResearchAgent/1.0"
    }

    # ONE shared HTTP client for the entire research batch.
    #
    # This allows connection reuse instead of creating
    # a new TCP connection for every webpage.
    async with httpx.AsyncClient(
        timeout=timeout,
        follow_redirects=True,
        headers=headers,
        limits=limits,
    ) as http_client:

        tasks = [
            gather_one(
                query,
                http_client,
            )
            for query in queries
        ]

        groups = await asyncio.gather(
            *tasks,
            return_exceptions=True,
        )

    all_sources = []

    for group in groups:

        if isinstance(group, Exception):
            continue

        all_sources.extend(group)

    return all_sources


# ============================================================
# 7. SYNCHRONOUS ENTRY POINT
# ============================================================

def parallel_search(
    queries: list[str],
) -> list[dict]:
    """
    Synchronous interface used by the LangGraph agent.

    Internally, the research process is asynchronous.
    """

    return asyncio.run(
        gather_parallel(queries)
    )


# ============================================================
# 8. DEDUPLICATION + FILTERING
# ============================================================

def deduplicate_and_filter(
    items: list[dict],
) -> list[dict]:
    """
    Remove duplicate and low-quality research sources.
    """

    seen_urls = set()
    seen_fingerprints = set()

    clean = []

    # Process highest-scoring Tavily results first.
    sorted_items = sorted(
        items,
        key=lambda x: x.get("score", 0),
        reverse=True,
    )

    for item in sorted_items:

        url = normalize_url(
            item.get("url", "")
        )

        content = " ".join(
            item.get("content", "").split()
        )

        # Reject missing URLs.
        if not url:
            continue

        # Reject extremely short content.
        if len(content) < 300:
            continue

        # Simple duplicate-content fingerprint.
        fingerprint = content[:500].lower()

        # Skip duplicate URLs or duplicate content.
        if url in seen_urls:
            continue

        if fingerprint in seen_fingerprints:
            continue

        seen_urls.add(url)
        seen_fingerprints.add(fingerprint)

        item["url"] = url
        item["content"] = content

        clean.append(item)

        # Respect the configured source limit.
        if len(clean) >= settings.max_sources:
            break

    return clean
