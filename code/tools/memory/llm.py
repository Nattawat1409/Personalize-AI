"""LLM client for the memory layer's own helper calls (router, write-back gate,
profile merge, summaries).

Same model family and same GOOGLE_API_KEY path as the generation call in
service/graph_llm.py. Kept separate on purpose: these calls are memory, not the
answer, so tuning them (here: temperature=0 for repeatable routing decisions)
cannot leak into the generation config that the benchmark locks.
"""

import os
from functools import lru_cache

from langchain_google_genai import ChatGoogleGenerativeAI

from config.memory import MEMORY_LLM_MODEL
from tools.general.build import load_env


@lru_cache(maxsize=1)
def get_memory_llm() -> ChatGoogleGenerativeAI:
    load_env()
    return ChatGoogleGenerativeAI(
        model=MEMORY_LLM_MODEL,
        google_api_key=os.environ.get("GOOGLE_API_KEY"),
        temperature=0,
    )
