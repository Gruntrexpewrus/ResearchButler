# Fetcher Module

This folder contains the modules responsible for retrieving raw data
from external sources.  Each module encapsulates the logic for
communicating with a particular API or service.  The fetchers return
plain Python data structures that can be consumed by the
summarisation layer or the web application.

## Files

* **`arxiv_fetcher.py`** – Implements `fetch_arxiv_papers()`, a helper
  function that queries the [arXiv API](https://info.arxiv.org/help/api/user-manual.html)
  for recent preprints matching a list of keywords.  It builds
  an Atom feed URL, requests the feed, parses it using `feedparser`
  and returns a list of dictionaries with titles, abstracts, authors,
  links and publication dates.  The official manual describes how
  search terms are constructed and provides sample code【99998283435305†L914-L935】.

* **`news_fetcher.py`** – Implements `fetch_news_articles()`, which
  constructs a Google News RSS query from a list of keywords,
  downloads the feed and extracts article titles, summaries, links and
  timestamps.  It uses `feedparser` for XML parsing.  No API key is
  required.

* **`journal_fetcher.py`** – Implements `fetch_recent_journals()`,
  which queries the [Crossref API](https://api.crossref.org)
  for recent journal articles matching the keywords.  The function
  assembles a query string, issues a GET request, parses the JSON
  response and extracts title, abstract (if present), author list,
  canonical URL and publication date.

All fetcher functions accept a list of keywords and a `max_results`
parameter.  They log errors and return an empty list if something
goes wrong rather than raising exceptions.  This defensive
programming ensures that the rest of the application continues to
function even when a data source is temporarily unavailable.