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
