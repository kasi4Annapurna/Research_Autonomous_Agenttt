from app.tools.search import normalize_url, deduplicate_and_filter

def test_normalize_url():
    assert normalize_url("HTTPS://Example.com/path/") == "https://example.com/path"

def test_deduplication():
    items = [
        {"url": "https://a.com/x", "content": "a" * 500, "score": 0.9},
        {"url": "https://a.com/x/", "content": "a" * 500, "score": 0.8},
        {"url": "https://b.com/y", "content": "b" * 500, "score": 0.7},
    ]
    assert len(deduplicate_and_filter(items)) == 2
