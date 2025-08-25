"""News article fetcher using Google News RSS feeds.

This module provides a helper to retrieve recent news articles
concerning a set of keywords from Google News RSS feeds.  It uses
FeedParser to parse the XML feed and returns a list of dictionaries
containing article metadata.  Google News RSS is publicly accessible
and does not require an API key.

Because Google News does not expose pagination via the RSS feed, the
``max_results`` parameter is applied after parsing.  The results are
ordered as they appear in the feed (usually most recent first).
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import List, Dict, Any

import requests
import feedparser

logger = logging.getLogger(__name__)


def fetch_news_articles(keywords: List[str], *, max_results: int = 5) -> List[Dict[str, Any]]:
    """Fetch news articles from Google News RSS matching the given keywords.

    Parameters
    ----------
    keywords:
        List of search terms to be combined using logical AND.  Terms
        are joined with ``+`` to form the query string.

    max_results:
        Maximum number of news items to return.

    Returns
    -------
    List[Dict[str, Any]]
        A list of dictionaries with the fields ``title``, ``summary``,
        ``link`` and ``published`` (a `datetime` object when
        possible).  If the request fails, an empty list is returned
        and an error is logged.
    """
    if not keywords:
        return []
    # Combine keywords into a single query string.  Spaces are replaced
    # with `+` according to the Google News RSS specification.
    query = '+'.join(keywords)
    # Build the RSS URL.  `hl`, `gl` and `ceid` control the locale and
    # edition of Google News (here set to US English).  You can
    # customise these parameters if you wish to fetch news in a different
    # language or region.
    rss_url = f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
    try:
        response = requests.get(rss_url, timeout=10)
        response.raise_for_status()
    except requests.RequestException as exc:
        logger.error("Failed to fetch Google News RSS: %s", exc)
        return []
    # Parse the RSS feed into a Python object
    feed = feedparser.parse(response.text)
    articles: List[Dict[str, Any]] = []
    for entry in feed.entries[:max_results]:
        # Convert the published timestamp (if present) into a datetime
        published = None
        if "published_parsed" in entry and entry.published_parsed:
            published = datetime(*entry.published_parsed[:6])
        articles.append(
            {
                "title": entry.title,
                "summary": getattr(entry, "summary", ""),
                "link": entry.link,
                "published": published,
            }
        )
    return articles
