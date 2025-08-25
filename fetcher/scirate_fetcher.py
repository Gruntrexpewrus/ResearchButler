"""Fetch top-rated arXiv papers from SciRate.

SciRate provides RSS feeds for arXiv categories ranked by community
votes over different time intervals.  This module exposes a helper
function to retrieve the top papers from the quantum physics
category (`quant-ph`) for a given time window (1 day or 7 days).
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import List, Dict, Any

import requests
import feedparser

logger = logging.getLogger(__name__)


def fetch_scirate_top(time_interval: str = "7", *, max_results: int = 3) -> List[Dict[str, Any]]:
    """Fetch top-rated arXiv papers from SciRate for the given time interval.

    Parameters
    ----------
    time_interval:
        The time window over which SciRate aggregates votes.  Use "7" for
        the past seven days or "1" for the past 24 hours.

    max_results:
        Maximum number of papers to return.

    Returns
    -------
    List[Dict[str, Any]]
        Each item is a dictionary with ``title``, ``summary``, ``link`` and
        ``published`` fields.  If the feed cannot be retrieved, an
        empty list is returned.
    """
    url = f"https://scirate.com/feed/arxiv/quant-ph?time_interval={time_interval}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except requests.RequestException as exc:
        logger.error("Failed to fetch SciRate feed: %s", exc)
        return []
    feed = feedparser.parse(response.text)
    papers: List[Dict[str, Any]] = []
    for entry in feed.entries[:max_results]:
        published = None
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            published = datetime(*entry.published_parsed[:6])
        papers.append(
            {
                "title": entry.title,
                "summary": getattr(entry, "summary", ""),
                "link": entry.link,
                "published": published,
            }
        )
    return papers