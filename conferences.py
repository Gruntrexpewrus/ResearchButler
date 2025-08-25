"""Static list of upcoming quantum computing conferences.

This module provides a list of notable upcoming conferences,
workshops and events in quantum computing and quantum information.
Each entry specifies the conference name, its dates and location,
and the submission deadline for papers or abstracts (if known).

These entries are maintained manually.  Feel free to update the
dates and add new conferences as they are announced.  Keeping
deadline information up to date can help researchers plan their
submissions.
"""

from __future__ import annotations

from typing import List, Dict

def get_upcoming_conferences() -> List[Dict[str, str]]:
    """Return a list of upcoming conferences and their deadlines.

    The conferences listed here are illustrative examples.  You
    should update them with real dates and venues as needed.  The
    fields are strings for simplicity; callers may parse them into
    datetime objects if necessary.
    """
    return [
        {
            "name": "Quantum Information Processing (QIP) 2025",
            "date": "2025-01-05 to 2025-01-10",
            "location": "Tokyo, Japan",
            "deadline": "2024-09-30",
        },
        {
            "name": "IEEE International Conference on Quantum Computing and Engineering (QCE) 2025",
            "date": "2025-03-15 to 2025-03-19",
            "location": "San Francisco, USA",
            "deadline": "2024-10-15",
        },
        {
            "name": "Quantum Tech 2025",
            "date": "2025-06-10 to 2025-06-12",
            "location": "London, UK",
            "deadline": "2025-02-01",
        },
        {
            "name": "APS March Meeting 2025",
            "date": "2025-03-03 to 2025-03-08",
            "location": "Chicago, USA",
            "deadline": "2024-11-14",
        },
        {
            "name": "NeurIPS 2025 (Quantum Machine Learning track)",
            "date": "2025-11-30 to 2025-12-05",
            "location": "Vancouver, Canada",
            "deadline": "2025-05-15",
        },
    ]