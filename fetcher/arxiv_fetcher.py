"""Utility functions for interacting with the arXiv API.

This module defines a simple helper to query the arXiv API for
recent papers matching a set of keywords.  It constructs a query
string using the `all:` search prefix and uses the Atom feed API
to fetch results in descending order of submission date.  The
results are parsed with the feedparser library and returned as
dictionaries suitable for further processing.

For details on constructing queries see the arXiv API user
manual【99998283435305†L914-L935】.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import List, Dict, Any

import requests
import feedparser

logger = logging.getLogger(__name__)


def fetch_arxiv_papers(keywords: List[str], *, max_results: int = 5) -> List[Dict[str, Any]]:
    """Fetch recent arXiv papers matching the given keywords.

    Parameters
    ----------
    keywords:
        A list of search terms.  These will be combined using the
        logical AND operator to narrow the search.  Each term is
        prefixed with ``all:`` so that the API searches across titles,
        abstracts, authors and other fields.

    max_results:
        Maximum number of papers to return.  The arXiv API will
        truncate results accordingly.

    Returns
    -------
    List[Dict[str, Any]]
        A list of dictionaries, each containing the fields:
        ``title``, ``summary``, ``authors``, ``link`` and
        ``published`` (as a `datetime` object).  If the API call
        fails, an empty list is returned and an error is logged.
    """
    if not keywords:
        return []
    # Build the search query by joining keywords with logical AND.  We
    # prefix each term with `all:` so that the API searches across
    # multiple fields (title, abstract, author, etc.).  Terms are
    # separated by `+AND+` according to the API specification.  See
    # arXiv API user manual for details【99998283435305†L914-L935】.
    search_terms = [f"all:{term}" for term in keywords]
    query = '+AND+'.join(search_terms)
    # Compose the API URL.  We sort results by the date they were
    # submitted to arXiv (most recent first) and request at most
    # `max_results` entries.
    url = (
        f"http://export.arxiv.org/api/query?search_query={query}"
        f"&sortBy=submittedDate&sortOrder=descending&max_results={max_results}"
    )
    try:
        # Send the HTTP GET request.  A timeout prevents hanging
        # indefinitely if the service is slow.
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except requests.RequestException as exc:
        # Log the error and return an empty list rather than raising.
        logger.error("Failed to fetch arXiv data: %s", exc)
        return []
    # Parse the Atom feed with feedparser.  The result has an
    # `entries` attribute containing individual feed entries.
    feed = feedparser.parse(response.text)
    results: List[Dict[str, Any]] = []
    for entry in feed.entries:
        # arXiv timestamps are ISO8601 strings; parse into datetime if possible
        try:
            published = datetime.strptime(entry.published, "%Y-%m-%dT%H:%M:%SZ")
        except Exception:
            published = None  # fallback if parsing fails
        # Build a dictionary for each paper.  We capture the title,
        # abstract (summary), list of authors, canonical link and
        # publication date.
        results.append(
            {
                "title": entry.title,
                "summary": entry.summary,
                "authors": [author.name for author in getattr(entry, "authors", [])],
                "link": entry.link,
                "published": published,
            }
        )
    return results
