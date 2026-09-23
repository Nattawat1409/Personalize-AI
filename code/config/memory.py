"""Personal-memory settings — the ONLY config the memory layer adds.

Retrieval config lives in config/vector.py, config/pinecone_core.py and
tools/general/build.py and is byte-identical to the baseline; nothing here may
change retrieval. See docs/HANDOFF_NEW_ARCHITECTURE.md §5.

Memory is stored PER USER under  <MEMORY_ROOT>/users/<user_id>/  so one user's
memory can never be read while answering for another (isolation is a tested
property — test/test_user_isolation.py).
"""

import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]  # repo root (code/config/memory.py)

# Runtime data, not source: gitignored. Overridable so tests never touch real data.
MEMORY_ROOT = Path(os.environ.get("PERSONALIZE_MEMORY_ROOT") or ROOT / "data" / "memory")
USERS_ROOT = MEMORY_ROOT / "users"

# user_id becomes a directory name, and reset_memory() deletes that directory,
# so it must never be able to contain a path separator or "..".
USER_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$")

# Genres a topic can be filed under (rules live in nodes/memory/decision_worth.py).
# python_topic was dropped: this repo is benchmarked against the production Cimie
# Pinecone (manufacturing/SCG-domain KM only), and general topic doesn't relate to business logic
CATEGORIES = ("business_logic", "general")

COMPRESS_AT_CHARS = 8000  # topic .md size that triggers a summary rewrite
ROUTER_MAX_TOPICS = 150  # above this the router prompt gets unwieldy
KEYWORDS_MAX = 8  # every keyword costs router-prompt tokens on every turn

EPISODIC_DAYS = 7  # daily logs loaded into context each turn

# A theme must recur on this many DISTINCT days within the window before it is
# written to the profile — the guard against inferring an interest from one mention.
RECURRING_INTEREST_MIN_OCCURRENCES = 3
RECURRING_INTEREST_WINDOW_DAYS = 7

# Model for the memory layer's own helper calls (router, write-back gate,
# summaries). Same model + same GOOGLE_API_KEY path as generation; kept as a
# separate constant because these calls are memory, not the answer.
MEMORY_LLM_MODEL = "gemini-2.5-flash"
