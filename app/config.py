from pathlib import Path

# 3 different genre of knowledge that contain within agent memory
CATEGORIES = ("business_logic", "python_topic", "general") 

MEMORY_ROOT = Path(__file__).resolve().parent / "memory"
TOPICS_INDEX_PATH = MEMORY_ROOT / "topics_index.json"
USER_PROFILE_PATH = MEMORY_ROOT / "user_profile.md"

COMPRESS_AT_CHARS = 8000
ROUTER_MAX_TOPICS = 150
LOG_ROUTER_REASON = True
