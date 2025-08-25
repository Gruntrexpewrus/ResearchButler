"""Fetch company-specific news from Google News RSS.

This module provides utilities for retrieving recent news articles
about specific quantum computing companies.  It builds upon the
existing Google News fetcher but filters results by a configurable
time window (in days) and tags each item with the company it came
from.  The functions return a mapping from company names to lists
of article dictionaries.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Mapping

from .news_fetcher import fetch_news_articles

logger = logging.getLogger(__name__)


def fetch_company_news(companies: List[str], days: int = 1, *, max_results: int = 3) -> Dict[str, List[Dict[str, Any]]]:
    """Fetch recent news for each company within a given time window.

    Parameters
    ----------
    companies:
        A list of company names.  Each company name will be used as
        the sole search term for Google News.

    days:
        The time window in days.  Articles older than this will be
        excluded.  Use ``days=1`` for daily news and ``days=7`` for
        weekly news.

    max_results:
        Maximum number of articles to return per company.  After
        filtering by date, results are truncated to this limit.

    Returns
    -------
    Dict[str, List[Dict[str, Any]]]
        A dictionary mapping each company name to a list of article
        dictionaries.  Each article dictionary includes ``title``,
        ``summary``, ``link``, ``published`` and ``company`` fields.
        If there are no articles for a company, an empty list is
        returned for that company.
    """
    results: Dict[str, List[Dict[str, Any]]] = {}
    if not companies:
        return results
    cutoff = datetime.utcnow() - timedelta(days=days)
    for company in companies:
        # Fetch raw articles using the existing news fetcher
        try:
            raw_articles = fetch_news_articles([company], max_results=10)
        except Exception as exc:
            logger.warning("Failed to fetch news for %s: %s", company, exc)
            results[company] = []
            continue
        filtered: List[Dict[str, Any]] = []
        for art in raw_articles:
            published = art.get("published")
            if published and published >= cutoff:
                filtered.append({**art, "company": company})
            if len(filtered) >= max_results:
                break
        results[company] = filtered
    return results