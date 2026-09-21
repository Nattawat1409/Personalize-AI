from pathlib import Path

# 3 different genre of knowledge that contain within agent memory
CATEGORIES = ("business_logic", "python_topic", "general") 

MEMORY_ROOT = Path(__file__).resolve().parent / "memory"
TOPICS_INDEX_PATH = MEMORY_ROOT / "topics_index.json"
USER_PROFILE_PATH = MEMORY_ROOT / "user_profile.md"

COMPRESS_AT_CHARS = 8000
ROUTER_MAX_TOPICS = 150
LOG_ROUTER_REASON = True

# Max KM source documents cited per turn, and kept on an index entry.
# v1 (POC) has no KM ingestion, so sources are always []. The plumbing exists
# so v2 retrieval can fill it without a schema migration. See docs/ARCHITECTURE.md §5.1
SOURCES_TOP_K = 5

# Keywords per topic, shown to the LLM router alongside title + one_liner.
# Capped because every keyword costs prompt tokens on EVERY turn, for EVERY topic.
KEYWORDS_MAX = 8

# --- Episodic layer (v2 Phase 5) — see docs/PLAN-v2.md §6, docs/ARCHITECTURE.md §5.3 ---
EPISODIC_ROOT = MEMORY_ROOT / "episodic"
EPISODIC_SUMMARY_PATH = EPISODIC_ROOT / "summary.md"
EPISODIC_DAYS = 7  # daily logs loaded into context on every turn

# Recurring Interests threshold: a theme must recur on at least this many
# DISTINCT days within the window to be written to user_profile.md. This is
# the guard against inferring an interest from a single mention.
RECURRING_INTEREST_MIN_OCCURRENCES = 3
RECURRING_INTEREST_WINDOW_DAYS = 7

# --- KM index (v2 Phase 1) — see docs/PLAN-v2.md §2, docs/ARCHITECTURE.md §5.1 ---
#
# A SEPARATE store from topics_index.json — never merge these. The LLM router
# (app/nodes/search_TopicIndex.py) is never given KM documents; app/memory/
# store.py never reads or writes anything under KM_INDEX_PATH. Nested under
# MEMORY_ROOT only for filesystem convenience, not because it's part of
# personal memory.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
KM_ROOT = PROJECT_ROOT / "mock_km"  # swap for the real KM folder in production
KM_MANIFEST_PATH = KM_ROOT / "manifest.json"  # built by mock_km/build_manifest.py
KM_INDEX_PATH = MEMORY_ROOT / "km_index"  # NOT topics_index.json
KM_TOP_K = 20  # hybrid retrieve depth (Phase 2)
KM_RERANK_K = 5  # after rerank (Phase 2)
