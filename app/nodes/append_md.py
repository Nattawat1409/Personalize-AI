from pydantic import BaseModel

from app.config import COMPRESS_AT_CHARS
from app.llm import llm
from app.memory.store import append_topic
from app.models.states.state import State

COMPRESS_PROMPT = """The conversation log below for one topic has grown large.
Rewrite it into:
1. A rolling summary (3-6 sentences) capturing everything learned about this
   topic across all turns so far.
2. A refreshed one-line description of the topic, suitable for a router that
   matches future questions to this topic by reading only that one line.

--- Full topic file ---
{content}
"""


class Compression(BaseModel):
    summary: str
    one_liner: str


def _llm_compress(full_text: str) -> tuple[str, str]:
    compressor = llm.with_structured_output(Compression)
    result: Compression = compressor.invoke(COMPRESS_PROMPT.format(content=full_text))
    return result.summary, result.one_liner


def append_md(state: State) -> dict:
    path = state["matched_topic_path"]
    result = append_topic(
        path_str=path,
        query=state["query"],
        answer=state["answer"],
        compress_at_chars=COMPRESS_AT_CHARS,
        llm_compress=_llm_compress,
    )

    trace_line = f"append_md: appended to '{path}', turn_count={result['turn_count']}"
    if result["compressed"]:
        trace_line += " (compressed summary + refreshed one_liner)"

    return {"trace": [trace_line]}
