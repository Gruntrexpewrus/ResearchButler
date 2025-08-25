# User Configuration

Each YAML file in this directory defines the preferences for one
dashboard user.  The filename (without the `.yaml` extension) must
match the username used in the URL.  For example, if you create
`users/charlie.yaml`, the dashboard will serve Charlie’s report at
`http://localhost:5000/user/charlie`.

## Configuration fields

* **`username`**: A human‑friendly name for the user.  It does not
  impact the URL.
* **`keywords`**: A list of phrases describing topics of interest.
  These are passed directly to the fetchers as search terms.  The
  more specific the phrases, the narrower the search results.
* **`companies`**: A list of company names.  These are appended to
  the news search terms so that business news related to the sector
  also appears in the report.
* **`people`**: A list of notable researchers or influencers.  Like
  `companies`, these names are added to the news search.
* **`max_results`**: A mapping specifying how many items to fetch
  from each source.  For example, `arxiv: 5` tells the arXiv
  fetcher to return at most five papers.

You can override any of the default values set in `config.yaml` by
specifying them here.  Any omitted fields fall back to the defaults.

## Adding a user

1. Copy the example configuration from `users/default.yaml` to a
   new file named `<username>.yaml`.
2. Edit the values to suit the user’s interests.  Save the file.
3. Restart the Flask application or refresh the dashboard.  The new
   user will appear on the index page.