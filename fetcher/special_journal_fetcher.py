"""Fetch journal articles from selected quantum computing journals.

Certain journals and series—such as Nature's portfolio and the
American Physical Society (APS) journals—are particularly relevant
to quantum computing and quantum information research.  This module
provides a helper to query the Crossref API for recent articles
from these outlets.  The caller may specify a list of keywords
which are combined with the journal filters to refine the search.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import List, Dict, Any

import requests

logger = logging.getLogger(__name__)

# A curated list of journal titles relevant to quantum computing.
SPECIAL_JOURNALS = [
    "Nature",
    "Nature Physics",
    "Nature Photonics",
    "Nature Communications",
    "Nature Quantum Information",
    "Nature Machine Intelligence",
    "Physical Review Letters",
    "Physical Review A",
    "Physical Review X",
    "Physical Review Research",
    "Quantum Science and Technology",
    "npj Quantum Information",
]


def fetch_special_journals(keywords: List[str], *, max_results: int = 5) -> List[Dict[str, Any]]:
    """Fetch recent papers from selected journals via Crossref.

    The function iterates over a predefined list of journal titles
    (``SPECIAL_JOURNALS``) and queries the Crossref API for each
    title in combination with the provided keywords.  Results from
    all journals are collected, sorted by publication date and
    truncated to the specified maximum number of items.

    Parameters
    ----------
    keywords:
        Keywords to include in the search.  They are joined using
        ``+`` (logical AND) when constructing the query string.

    max_results:
        Total number of results to return across all journals.

    Returns
    -------
    List[Dict[str, Any]]
        A list of dictionaries with ``title``, ``summary``, ``authors``,
        ``link``, ``published`` and ``journal`` fields.  If no data
        can be retrieved, an empty list is returned.
    """
    if not keywords:
        return []
    query = '+'.join(keywords)
    all_items: List[Dict[str, Any]] = []
    for journal in SPECIAL_JOURNALS:
        # Build the API URL with a filter on the container title
        # According to Crossref docs, container-title filter can be
        # specified as `filter=container-title:<journal>`.
        url = (
            f"https://api.crossref.org/works?query={query}"
            f"&filter=container-title:{journal.replace(' ', '+')}"
            f"&sort=published&order=desc&rows=5"
        )
        try:
            resp = requests.get(
                url, timeout=10, headers={"User-Agent": "QuantumInsights/0.1"}
            )
            resp.raise_for_status()
        except requests.RequestException as exc:
            logger.warning("Failed to fetch special journal data for %s: %s", journal, exc)
            continue
        try:
            data = resp.json()
        except Exception as exc:
            logger.warning("Failed to parse JSON for special journal %s: %s", journal, exc)
            continue
        items = data.get("message", {}).get("items", [])
        for item in items:
            title = item.get("title", [""])[0]
            summary = item.get("abstract") or ""
            authors_data = item.get("author", [])
            authors: List[str] = []
            for auth in authors_data:
                parts = [auth.get("given", ""), auth.get("family", "")]
                authors.append(" ".join(part for part in parts if part))
            link = item.get("URL")
            # Determine the publication date similarly to the general journal fetcher
            published = None
            for date_key in ["published-print", "published-online", "issued"]:
                if date_key in item and "date-parts" in item[date_key]:
                    parts = item[date_key]["date-parts"][0]
                    try:
                        if len(parts) >= 3:
                            published = datetime(parts[0], parts[1], parts[2])
                        elif len(parts) == 2:
                            published = datetime(parts[0], parts[1], 1)
                        elif len(parts) == 1:
                            published = datetime(parts[0], 1, 1)
                    except Exception:
                        pass
                    if published:
                        break
            container = item.get("container-title", [])
            journal_title = container[0] if container else journal
            all_items.append(
                {
                    "title": title,
                    "summary": summary,
                    "authors": authors,
                    "link": link,
                    "published": published,
                    "journal": journal_title,
                }
            )
    # Sort across all journals by date and limit the number of results
    all_items.sort(
        key=lambda x: x.get("published", datetime.min), reverse=True
    )
    return all_items[:max_results]