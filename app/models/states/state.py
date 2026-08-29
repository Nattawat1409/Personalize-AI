import operator
from typing import Annotated, Literal, Optional

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict

Category = Literal["business_logic", "python_topic", "general"]


class State(TypedDict, total=False):
    # --- input ---
    query: str

    # --- memory read ---
    user_profile: str
    matched_topic_id: Optional[str]
    matched_topic_path: Optional[str]
    match_reason: str
    topic_content: str

    # --- generation ---
    context: str
    messages: Annotated[list[AnyMessage], add_messages]
    answer: str

    # KM documents cited for this turn, max SOURCES_TOP_K.
    # v1 (POC) has no KM ingestion, so this is always [] — writing anything here
    # without real retrieval would be a fabricated citation.
    # v2 fills it from the rerank stage. See docs/ARCHITECTURE.md §5.1
    sources: list[dict]

    # --- memory write ---
    memory_action: Literal["skip", "append", "create", "profile"]
    memory_category: Category
    topic_title: str
    topic_one_liner: str
    topic_summary: str
    topic_keywords: list[str]
    profile_update: str

    # --- observability ---
    trace: Annotated[list[str], operator.add]
