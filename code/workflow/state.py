"""State passed between the memory nodes (read path and write-back path).

A plain dict, not a LangGraph state: the baseline pipeline is a single async
function (see service/graph_llm.py) and the memory layer plugs into it at two
points, so there is no graph runtime here. `trace` lines are concatenated by
service/memory_service.py::apply().
"""

from typing import Literal, Optional

from typing_extensions import TypedDict

Category = Literal["business_logic", "general"]


class State(TypedDict, total=False):
    # --- input ---
    user_id: str
    query: str
    answer: str  # the answer the user actually saw (write-back only)

    # --- memory read ---
    user_profile: str
    episodic_context: str
    episodic_paths: list[str]
    matched_topic_id: Optional[str]
    matched_topic_path: Optional[str]
    match_reason: str
    topic_content: str

    # --- memory write ---
    memory_action: Literal["skip", "append", "create", "profile"]
    memory_category: Category
    topic_title: str
    topic_one_liner: str
    topic_summary: str
    topic_keywords: list[str]
    profile_update: str
    episodic_gist: str
    episodic_category: str

    # --- observability ---
    trace: list[str]
