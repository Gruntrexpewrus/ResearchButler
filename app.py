"""Flask application providing a web dashboard for quantum computing insights.

This module wires together the fetcher modules, the summariser and the
Flask web framework.  It discovers user configuration files in the
``users`` directory, builds personalised reports on demand and
serves them via simple HTML templates.  Additional configuration and
presentation logic can be added here as needed.
"""

from __future__ import annotations

import os
from datetime import datetime
import yaml
import logging
from functools import lru_cache
from typing import Dict, Any, List

from flask import Flask, render_template, url_for, redirect, abort

from fetcher import fetch_arxiv_papers, fetch_news_articles, fetch_recent_journals
from summarizer.summarizer import Summarizer
from trivia import get_trivia_pair

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create the Flask application.  We specify the template and static
# folders explicitly because our HTML and assets live under the
# `dashboard` subdirectory rather than the default `templates` and
# `static` directories.  `BASE_DIR` is defined below.
app = Flask(
    __name__,
    template_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), "dashboard", "templates"),
    static_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), "dashboard", "static"),
)

# Directory paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
USERS_DIR = os.path.join(BASE_DIR, "users")
CONFIG_FILE = os.path.join(BASE_DIR, "config.yaml")

# Lazy initialisation of the summariser (so the model is only loaded when needed)
summariser = Summarizer()


def load_yaml_file(path: str) -> Dict[str, Any]:
    """Load a YAML file and return its contents as a dictionary.

    If the file is missing or contains invalid YAML, this helper
    returns an empty dictionary rather than raising an exception.  This
    defensive approach prevents a single corrupt configuration file
    from bringing down the entire application.
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except FileNotFoundError:
        logger.warning("Configuration file %s not found", path)
    except yaml.YAMLError as exc:
        logger.error("Failed to parse YAML file %s: %s", path, exc)
    return {}


@lru_cache(maxsize=None)
def get_default_config() -> Dict[str, Any]:
    """Load and cache the default configuration from `config.yaml`.

    The result is cached using `functools.lru_cache` so that the file
    is only read once per process.  If the file is missing, an empty
    dictionary is returned.  The default config defines fallback
    values for keywords, result limits, etc., which are used when
    individual user configurations omit these fields.
    """
    return load_yaml_file(CONFIG_FILE).get("default", {})


def list_users() -> List[str]:
    """Return a list of user *slugs* (filenames without extensions).

    A slug corresponds to the YAML filename in the ``users/`` folder
    minus the ``.yaml`` suffix.  The actual display name for a user
    is defined inside the YAML file under the keys ``username`` or
    ``name``.  This helper only returns the slugs so that callers can
    subsequently load each configuration and extract the display name
    where appropriate.  The resulting list is sorted alphabetically
    for a stable ordering on the index page.
    """
    if not os.path.isdir(USERS_DIR):
        return []
    slugs: List[str] = []
    for fname in os.listdir(USERS_DIR):
        if fname.endswith(".yaml"):
            slugs.append(os.path.splitext(fname)[0])
    return sorted(slugs)


def load_user_config(username: str) -> Dict[str, Any]:
    """Load a user's configuration and merge it with defaults.

    This function loads the default configuration and then overlays it
    with values from the user’s YAML file.  Nested dictionaries (such
    as `max_results`) are merged one key at a time.  Flat keys
    completely overwrite the default.  The merged configuration is
    returned as a new dictionary.
    """
    default = get_default_config().copy()
    user_file = os.path.join(USERS_DIR, f"{username}.yaml")
    user_cfg = load_yaml_file(user_file)
    # Merge dictionaries (shallow).  User config overrides default.
    # For nested dicts like max_results, merge keys individually.
    for key, value in user_cfg.items():
        if isinstance(value, dict) and isinstance(default.get(key), dict):
            merged = default[key].copy()
            merged.update(value)
            default[key] = merged
        else:
            default[key] = value
    return default


def build_report(config: Dict[str, Any], username: str) -> Dict[str, Any]:
    """Fetch data from all sources, rank them and summarise according to the config.

    In addition to summarising each item, this function calculates a
    simple relevance score for papers and news articles based on
    keyword occurrences and recency.  Items are sorted by descending
    score.  The top two items per category receive a longer summary
    (max_length=200), while the remaining items are summarised
    more concisely (max_length=80).  You can tune these numbers in
    future revisions.

    The config is expected to contain ``keywords``, ``companies``,
    ``people`` and ``max_results`` entries.  Keywords determine the
    core search terms; companies and people of interest are appended
    to the news search to broaden coverage.
    """
    keywords: List[str] = config.get("keywords", [])
    companies: List[str] = config.get("companies", [])
    people: List[str] = config.get("people", [])
    max_results: Dict[str, int] = config.get("max_results", {})

    reports: Dict[str, List[Dict[str, Any]]] = {}

    def relevance_score(item: Dict[str, Any], search_terms: List[str]) -> float:
        """Compute a simple relevance score based on keyword matches and recency.

        Each occurrence of a keyword in the title contributes 1.0 to the
        score; occurrences in the summary contribute 0.5.  The score is
        divided by the age of the item in days plus one, so newer
        articles receive slightly higher scores.
        """
        score = 0.0
        title = (item.get("title") or "").lower()
        summary = (item.get("summary") or "").lower()
        for term in search_terms:
            term_lower = term.lower()
            score += title.count(term_lower) * 1.0
            score += summary.count(term_lower) * 0.5
        # Add small recency factor
        published = item.get("published")
        if published:
            days_old = (datetime.utcnow() - published).days
            score = score / (days_old + 1)
        return score

    # Helper to process items: score, sort and summarise
    def process_items(raw_items: List[Dict[str, Any]], max_len_top: int, max_len_rest: int) -> List[Dict[str, Any]]:
        scored = [
            (relevance_score(item, keywords + companies + people), idx, item)
            for idx, item in enumerate(raw_items)
        ]
        # Sort by score descending, then original order to stabilise ties
        scored.sort(key=lambda x: (-x[0], x[1]))
        processed: List[Dict[str, Any]] = []
        for i, (_, _, item) in enumerate(scored):
            summary_text = item.get("summary", "")
            max_len = max_len_top if i < 2 else max_len_rest  # top 2 items get longer summary
            # Clean HTML tags for journals
            plain = summary_text.replace("<jats:p>", "").replace("</jats:p>", "").replace("<p>", "").replace("</p>", "")
            concise = summariser.summarize(plain, max_length=max_len, min_length=max_len // 3) if plain else ""
            processed.append({**item, "summary": concise})
        return processed

    # Fetch data
    from datetime import datetime  # local import to avoid circular
    arxiv_max = max_results.get("arxiv", 5)
    journal_max = max_results.get("journals", 5)
    news_max = max_results.get("news", 5)

    arxiv_raw = fetch_arxiv_papers(keywords, max_results=arxiv_max)
    journal_raw = fetch_recent_journals(keywords, max_results=journal_max)
    news_terms = keywords + companies + people
    news_raw = fetch_news_articles(news_terms, max_results=news_max)

    reports["arxiv"] = process_items(arxiv_raw, 200, 80)
    reports["journals"] = process_items(journal_raw, 200, 80)
    reports["news"] = process_items(news_raw, 200, 80)

    # Fetch additional journals from selected outlets (Nature, APS, etc.)
    try:
        from fetcher.special_journal_fetcher import fetch_special_journals  # import locally to avoid circular
        special_journal_raw = fetch_special_journals(keywords, max_results=max_results.get("special_journals", 5))
        reports["special journals"] = process_items(special_journal_raw, 200, 80)
    except Exception as exc:
        logger.warning("Failed to fetch special journals: %s", exc)

    # Company‑specific news (daily and weekly)
    try:
        from fetcher.company_news_fetcher import fetch_company_news
        # Daily news (last 24 hours)
        company_daily_raw = fetch_company_news(companies, days=1, max_results=3)
        # Summarise news per company but preserve the grouping.  Each company gets its
        # own list of summarised items.  We still prioritise the first two items for
        # longer summaries within each company.
        company_daily_processed: Dict[str, List[Dict[str, Any]]] = {}
        for comp, items in company_daily_raw.items():
            if not items:
                company_daily_processed[comp] = []
                continue
            # Summarise using the same process: top two items get longer summaries
            processed = process_items(items, 200, 80)
            company_daily_processed[comp] = processed
        reports["company_daily"] = company_daily_processed
        # Weekly news (last 7 days)
        company_weekly_raw = fetch_company_news(companies, days=7, max_results=3)
        company_weekly_processed: Dict[str, List[Dict[str, Any]]] = {}
        for comp, items in company_weekly_raw.items():
            if not items:
                company_weekly_processed[comp] = []
                continue
            processed = process_items(items, 200, 80)
            company_weekly_processed[comp] = processed
        reports["company_weekly"] = company_weekly_processed
    except Exception as exc:
        logger.warning("Failed to fetch company news: %s", exc)

    # Include SciRate top papers (quant‑ph) for past 7 days and past 24 hours
    try:
        from fetcher.scirate_fetcher import fetch_scirate_top  # import here to avoid circular
        scirate_7d = fetch_scirate_top("7", max_results=3)
        scirate_1d = fetch_scirate_top("1", max_results=3)
        # SciRate items are already curated; we include them as is
        reports["scirate_7d"] = scirate_7d
        reports["scirate_24h"] = scirate_1d
    except Exception as exc:
        logger.warning("Failed to fetch SciRate data: %s", exc)

    # After assembling reports, analyse trends to provide advice
    analysis = analyse_trends(reports, keywords, username)
    # Generate a bar chart for keyword trends and save it into the static folder.
    trend_plot_path = None
    try:
        from matplotlib import pyplot as plt
        import numpy as np  # type: ignore
        # Only generate a plot if there are keywords
        if keywords:
            counts = analysis.get("counts", {})
            prev_counts = analysis.get("previous", {})
            labels = [kw for kw in keywords]
            current_vals = [counts.get(kw, 0) for kw in labels]
            prev_vals = [prev_counts.get(kw, 0) for kw in labels]
            x = np.arange(len(labels))
            width = 0.35
            fig, ax = plt.subplots(figsize=(max(4, len(labels)*1.2), 3))
            ax.bar(x - width/2, prev_vals, width, label='Yesterday', color='#8faadc')
            ax.bar(x + width/2, current_vals, width, label='Today', color='#305491')
            ax.set_ylabel('Mentions')
            ax.set_title('Keyword Frequency Comparison')
            ax.set_xticks(x)
            ax.set_xticklabels(labels, rotation=45, ha='right')
            ax.legend()
            plt.tight_layout()
            static_dir = os.path.join(BASE_DIR, 'dashboard', 'static')
            os.makedirs(static_dir, exist_ok=True)
            filename = f'trends_{username}.png'
            filepath = os.path.join(static_dir, filename)
            fig.savefig(filepath)
            plt.close(fig)
            trend_plot_path = filename
    except Exception as exc:
        logger.warning("Failed to generate trend plot: %s", exc)
    # Add two trivia items (a fact and a dynamic joke) to lighten the report
    fact, joke = get_trivia_pair()
    # Also provide upcoming conference information
    try:
        from conferences import get_upcoming_conferences
        conferences_list = get_upcoming_conferences()
    except Exception as exc:
        logger.warning("Failed to load conferences: %s", exc)
        conferences_list = []
    # Compute a TL;DR by concatenating all titles and summaries and summarising the
    # result.  This provides a high‑level overview of the day's findings.  The
    # summariser will automatically truncate to the specified max_length.
    try:
        tldr_source_parts: List[str] = []
        for category, items in reports.items():
            # Company news is a mapping from company to list of items
            if category in {"company_daily", "company_weekly"}:
                for comp_items in items.values():
                    for it in comp_items:
                        tldr_source_parts.append(f"{it.get('title','')}. {it.get('summary','')}")
            elif isinstance(items, list):
                for it in items:
                    tldr_source_parts.append(f"{it.get('title','')}. {it.get('summary','')}")
        full_text = " ".join(tldr_source_parts)
        tldr_summary = summariser.summarize(full_text, max_length=300, min_length=100) if full_text else ""
    except Exception as exc:
        logger.warning("Failed to generate TLDR summary: %s", exc)
        tldr_summary = ""
    return {
        "reports": reports,
        "analysis": analysis,
        "trivia_fact": fact,
        "trivia_joke": joke,
        "conferences": conferences_list,
        "tldr": tldr_summary,
        "trend_plot": trend_plot_path,
    }


def analyse_trends(reports: Dict[str, Any], keywords: List[str], username: str) -> Dict[str, Any]:
    """Compute keyword frequency trends, returning counts, previous counts and messages.

    This function flattens all titles and summaries in the report into a list
    of strings, counts how many times each keyword appears and compares
    these counts with those from the previous run (stored under
    ``data/<username>_trends.json``).  A list of messages describes
    increases or decreases, and the current counts are persisted for
    use on the next invocation.

    ``reports`` is a dictionary of category names to either lists of
    items or mappings from company names to lists of items.  Items are
    expected to be dictionaries with ``title`` and ``summary`` keys.
    """
    import json
    from collections import Counter
    # Gather all text from the reports.  Company news sections (daily/weekly)
    # are mappings from company to list of article dicts, whereas other
    # sections are simple lists.  We extract title and summary for each.
    texts: List[str] = []
    for category, category_items in reports.items():
        if category in {"company_daily", "company_weekly"}:
            for comp_items in category_items.values():
                for it in comp_items:
                    text = f"{it.get('title', '')} {it.get('summary', '')}"
                    texts.append(text)
        else:
            # category_items should be a list of dicts
            for it in category_items:
                text = f"{it.get('title', '')} {it.get('summary', '')}"
                texts.append(text)
    # Count keyword occurrences
    counter = Counter()
    for text in texts:
        lower = text.lower()
        for kw in keywords:
            if kw.lower() in lower:
                counter[kw] += 1
    # Prepare data directory and previous counts file
    data_dir = os.path.join(BASE_DIR, "data")
    os.makedirs(data_dir, exist_ok=True)
    trend_file = os.path.join(data_dir, f"{username}_trends.json")
    prev_counts: Dict[str, int] = {}
    try:
        with open(trend_file, "r", encoding="utf-8") as f:
            prev_counts = json.load(f)
    except FileNotFoundError:
        prev_counts = {}
    # Build messages describing changes
    messages: List[str] = []
    for kw in keywords:
        prev = prev_counts.get(kw, 0)
        curr = counter.get(kw, 0)
        if curr > prev:
            messages.append(f"Interest in '{kw}' appears to be increasing (from {prev} to {curr} articles)")
        elif curr < prev:
            messages.append(f"Interest in '{kw}' has declined (from {prev} to {curr} articles)")
    if not messages:
        messages.append("Topic frequencies are stable compared with yesterday.")
    # Persist current counts for next run
    try:
        with open(trend_file, "w", encoding="utf-8") as f:
            json.dump(counter, f)
    except Exception as exc:
        logger.warning("Failed to save trend data: %s", exc)
    return {
        "counts": dict(counter),
        "previous": prev_counts,
        "messages": messages,
    }


@app.route("/")
def index():
    """Render the home page listing all available users.

    The index page shows a list of users for whom configuration
    files exist.  Each entry displays the user’s preferred name
    (the ``username`` or ``name`` field from their YAML file) and
    links to their report using the slug derived from the filename.
    """
    user_slugs = list_users()
    display_users: List[Dict[str, str]] = []
    for slug in user_slugs:
        cfg = load_user_config(slug)
        # Prefer explicit keys for display; fall back to the slug
        display_name: str = (
            cfg.get("username")
            or cfg.get("name")
            or slug
        )
        display_users.append({"slug": slug, "name": display_name})
    return render_template("index.html", users=display_users)


@app.route("/user/<username>")
def user_report(username: str):
    """Render a detailed report for a specific user.

    ``username`` here refers to the slug derived from the YAML
    filename.  Before rendering, we verify that a configuration
    exists for the slug and then load the configuration, build the
    report data and extract the user’s preferred display name.  The
    display name is passed separately so that templates can show
    the human‑friendly name while still using the slug for routing.
    """
    users = list_users()
    if username not in users:
        abort(404)
    config = load_user_config(username)
    # Determine the display name from the config (username or name)
    display_name: str = (
        config.get("username")
        or config.get("name")
        or username
    )
    result = build_report(config, username)
    return render_template(
        "user.html",
        username=username,
        display_name=display_name,
        reports=result["reports"],
        analysis=result["analysis"],
        trivia_fact=result["trivia_fact"],
        trivia_joke=result["trivia_joke"],
        conferences=result.get("conferences", []),
        tldr=result.get("tldr", ""),
        trend_plot=result.get("trend_plot"),
    )


if __name__ == "__main__":
    # When run directly, start the Flask development server
    app.run(debug=True)
