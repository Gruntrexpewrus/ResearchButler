"""Aggregated fetcher functions.

This package exposes the public functions for fetching data from
different sources (arXiv, Google News and Crossref).  Importing
these names here makes them available as `fetcher.fetch_arxiv_papers`,
etc.
"""

from .arxiv_fetcher import fetch_arxiv_papers  # noqa: F401
from .news_fetcher import fetch_news_articles  # noqa: F401
from .journal_fetcher import fetch_recent_journals  # noqa: F401

__all__ = [
    "fetch_arxiv_papers",
    "fetch_news_articles",
    "fetch_recent_journals",
]
