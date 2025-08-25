# Quantum Insights Dashboard

**Research Butler** is a Python‑based
web application that
aggregates and summarises recent developments in a chosen scientific
field – initially configured for **quantum computing**.  It scrapes
fresh preprints from arXiv, recent publications indexed by Crossref
(journals), and news articles about companies in the sector.  The
content is condensed using a locally running large language model (LLM)
so that busy researchers start their day with a concise overview of
what happened overnight.

## Features

* **Multi‑source aggregator:** Collects articles from the arXiv API,
  Crossref API and Google News RSS feeds.  Each source can be
  configured with search keywords per user.
* **Local LLM summarisation:** Utilises the open‑source
  `facebook/bart‑large‑cnn` summarisation model via the
  [Hugging Face Transformers](https://huggingface.co/docs/transformers/en/tasks/summarization)
  pipeline.  This allows you to run summaries on your own machine
  without sending data to a third party.  You can swap the model for
  another summariser if desired.
* **Per‑user customisation:** Each user has their own YAML
  configuration file under `users/` specifying keywords of interest,
  companies and people to watch, and the maximum number of results to
  fetch per source.  More users can be added simply by dropping a new
  YAML file into this directory.
* **Web dashboard:** A lightweight Flask application serves a
  dashboard that lists all configured users and shows a daily report
  summarising the latest papers and news for the selected user.
* **Extensible design:** The architecture separates data fetching
  (`fetcher/`), summarisation (`summariser/`), configuration and
  presentation.  This makes it straightforward to add new
  information sources, change the LLM model or adapt the front‑end
  design.
* **Relevance ranking and variable summaries:** The dashboard
  automatically ranks fetched items by how closely they match your
  keywords and how recent they are.  The top two items in each
  category receive a longer summary, while the remainder are
  condensed into a sentence or two.
* **Trend analysis and visualisation:** A trend card compares today’s
  keyword frequencies to yesterday’s, generates a bar chart to visualise
  gains or losses, and highlights topics that are gaining or losing
  momentum.
* **Daily TL;DR and trivia:** Each report begins with a high‑level summary
  (300 words or fewer) capturing the essence of all fetched items.  A
  trivia section adds a fun fact and a one‑liner joke to lighten the mood.

## Installation

1. Clone this repository and change into the project directory:

   ```bash
   git clone https://github.com/Gruntrexpewrus/ResearchButler.git
   cd ResearchButler
   ```

2. Create a **Conda** environment (recommended) and install dependencies:

   ```bash
    conda create -n research_butler python=3.9 -y
    conda activate research_butler
    python -m pip install -r requirements.txt   # or: conda env update -f environment.yml
    python app.py
   ```

   The `requirements.txt` file lists Flask, requests, PyYAML, schedule,
   transformers and `matplotlib` for trend plots.  When installing
   `transformers`, the appropriate PyTorch version will be pulled in.
   If you wish to use a GPU for faster summarisation, ensure you
   install a CUDA‑enabled build of PyTorch before running the pip command.

**Hardware requirements:** The application runs on a regular CPU.
Downloading the LLM weights (about 1 GB) and summarising long
documents may take several seconds on first use.  If your machine has
a CUDA‑enabled GPU and you have installed a GPU‑enabled version of
PyTorch, the summariser will use the GPU automatically, which
dramatically speeds up inference.  A GPU is **not required** to run
the dashboard.

3. Download the summarisation model (this happens automatically the
   first time you run the application).  Note that the model weights
   (around 1 GB) will be stored in your `~/.cache/huggingface`
   directory.

4. Start the development server:

   You can run the app directly with Python, which avoids having to
   set the `FLASK_APP` environment variable:

   ```bash
      conda create -n research_butler python=3.9 -y
      conda activate research_butler
      python -m pip install -r requirements.txt   # or: conda env update -f environment.yml
      python app.py
   ```

   Alternatively, you can use Flask’s CLI:

   ```bash
   export FLASK_APP=app.py
   flask run
   ```

   By default the server runs on `http://127.0.0.1:5000`.  Open this
   URL in your browser to see the dashboard.

## Usage

### Configuring users

User configuration files live in the `users/` directory.  Each YAML
file describes a username and their interests.  For example,
`users/default.yaml` looks like this:

```yaml
username: alice
keywords:
  - quantum computing
  - quantum machine learning
companies:
  - IBM
  - Google Quantum
people:
  - John Preskill
  - Scott Aaronson
max_results:
  arxiv: 5
  journals: 5
  news: 5
```

You can create additional files such as `users/bob.yaml` with your
own values.  When you visit `http://localhost:5000`, the index page
lists all detected users.  Clicking on a username shows their
personalised daily summary.

### Folder documentation

Each major folder in this project includes its own `README.md` file
with more detailed explanations and instructions.  Refer to these
documents if you wish to extend or modify the fetchers, the
summarisation engine, the dashboard templates, or the user
configuration format.

### Running on a schedule

To automate updates each morning, you can run the `update_reports.py`
script (not included in this prototype) via `cron` or the
`schedule` library.  The dashboard always reads the latest data
directly from the APIs, so running the script is optional for this
version.  For production you might cache results and refresh them
overnight to avoid hitting API rate limits during the day.

## Architecture overview

* `fetcher/`: Contains modules for fetching data from different
  sources.  `arxiv_fetcher.py` queries the arXiv API using the
  Atom feed API (examples for using `urllib` are provided in
  the official arXiv documentation【99998283435305†L914-L935】).  `news_fetcher.py`
  retrieves news articles from Google News RSS feeds, and
  `journal_fetcher.py` queries the Crossref API for recent journal
  publications.
* `summarizer/`: Wraps a Hugging Face summarisation pipeline.  The
  chosen model (`facebook/bart‑large‑cnn`) can summarise long
  abstracts or news articles into short, readable paragraphs using
  abstractive techniques【994451517533277†L104-L111】.
* `app.py`: Main Flask application that loads user configurations,
  collects fresh data via the fetchers, runs summaries through the
  local LLM and renders the results using Jinja2 templates.
* `dashboard/templates/`: Contains HTML templates for the dashboard.
* `dashboard/static/`: Contains CSS or JavaScript assets.

## Citation

This project uses the arXiv API to retrieve recent preprints.  The
official user manual describes how to construct queries, including
examples of using the Python `urllib` module【99998283435305†L914-L935】.
The summarisation feature is built on top of the Hugging Face
Transformers library.  Their documentation explains that
summarisation generates a shorter version of a document that
captures the important information through an abstractive
sequence‑to‑sequence model【994451517533277†L104-L111】.
