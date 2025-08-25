"""Journal article fetcher using the Crossref API.

Crossref provides a public API that returns bibliographic metadata for
articles, conference proceedings and other scholarly works.  This
module defines a helper to query Crossref for the latest journal
publications matching a set of keywords.  We filter results by
publication date via sorting and limit the number returned.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import List, Dict, Any

import requests

logger = logging.getLogger(__name__)


def fetch_recent_journals(keywords: List[str], *, max_results: int = 5) -> List[Dict[str, Any]]:
    """Fetch recent journal articles from Crossref.

    Parameters
    ----------
    keywords:
        List of search keywords.  They are concatenated with ``+``
        characters to form the query string.  Crossref's API accepts
        simple free text search for titles, authors and abstracts.

    max_results:
        Maximum number of journal articles to return.

    Returns
    -------
    List[Dict[str, Any]]
        A list of dictionaries containing ``title``, ``summary``,
        ``authors``, ``link`` and ``published`` fields.  If no results
        are found or the API call fails, the function returns an empty list.
    """
    if not keywords:
        return []
    # Assemble the search query by joining keywords with `+`.  Crossref
    # interprets this as a space (AND) in free‑text search.
    query = '+'.join(keywords)
    # Construct the API URL.  We sort results by the publication date
    # (`published`) in descending order and limit the number of rows.
    url = (
        f"https://api.crossref.org/works?query={query}&sort=published&order=desc"
        f"&rows={max_results}"
    )
    try:
        # Request the Crossref works endpoint.  A custom User‑Agent
        # header identifies your application and is considered good
        # practice when using public APIs.
        response = requests.get(
            url, timeout=10, headers={"User-Agent": "QuantumInsights/0.1"}
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        logger.error("Failed to fetch Crossref data: %s", exc)
        return []
    # Parse the JSON response.  Crossref returns a nested structure
    # where the actual works are under `message.items`.
    try:
        data = response.json()
    except Exception as exc:
        logger.error("Failed to parse Crossref response: %s", exc)
        return []
    items = data.get("message", {}).get("items", [])
    results: List[Dict[str, Any]] = []
    for item in items[:max_results]:
        # The title is returned as a list of strings; take the first
        title = item.get("title", [""])[0]
        # Abstracts are optional and may include HTML tags such as
        # `<jats:p>`; we leave cleaning to the caller.
        summary = item.get("abstract") or ""
        # Build a list of author names (given + family)
        authors_data = item.get("author", [])
        authors = []
        for auth in authors_data:
            name_parts = [auth.get("given", ""), auth.get("family", "")]
            authors.append(" ".join(part for part in name_parts if part))
        link = item.get("URL")
        # Determine the publication date.  Crossref may provide several
        # keys; we check them in order of preference and construct a
        # datetime accordingly.  If the day or month is missing, we
        # fall back to the first day of the period.
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
        # Container title provides the journal or conference name.  It is
        # returned as a list of strings; take the first if available.
        journal_name = item.get("container-title", [])
        journal = journal_name[0] if journal_name else ""
        results.append(
            {
                "title": title,
                "summary": summary,
                "authors": authors,
                "link": link,
                "published": published,
                "journal": journal,
            }
        )
    return results
