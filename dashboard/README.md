# Dashboard Module

This folder contains the web interface for the Quantum Insights
Dashboard.  It is built using [Flask](https://flask.palletsprojects.com/)
and Jinja2 templates.  The interface presents a list of configured
users and displays a personalised report for each user.

## Structure

* **`templates/`** – Contains HTML files using the Jinja2 syntax.
  * `base.html` defines the common page layout, including a header
    and a link to the CSS file.
  * `index.html` lists all available users (each corresponds to a
    YAML file in the `users/` directory).  Selecting a user leads to
    their report page.
  * `user.html` displays the summarised articles and news for a
    specific user and includes a trend analysis and trivia section.
* **`static/`** – Contains static assets such as `style.css`.  You
  can modify this CSS to customise the look and feel of the
  dashboard.

## How it works

The `app.py` file in the repository root creates a Flask application
and registers the routes:

* `/` – Lists all users.  It reads the `users/` folder to identify
  available YAML configuration files.
* `/user/<username>` – Generates a personalised report.  The
  application loads the user’s configuration, fetches data from
  arXiv, Crossref and Google News, summarises each item using the
  `Summarizer`, ranks them by relevance and displays the results on
  this page.  Trend analysis compares today’s keyword frequencies
  against the previous day and outputs messages about increasing or
  declining interest.

Feel free to extend the templates or CSS to improve the user
experience.  The current styling is deliberately simple to keep the
project lightweight and easy to understand.