from langchain_core.messages import SystemMessage

from app.llm import llm
from app.models.states.state import State

SYSTEM_PROMPT = """You are a helpful personal assistant with memory of past
conversations with this specific user. You may be given:
- "What you know about this user" — their profile/preferences
- "Your notes from previous conversations on this topic" — what you learned
  last time this subject came up

Use these naturally, as a person who remembers would. If prior notes on this
topic are present, briefly acknowledge the continuity (e.g. "Last time we
discussed..." or "Building on what we covered before...") before answering.
If no prior notes are present, just answer normally — do not pretend to
remember something you don't.
"""


def generate_answer(state: State) -> dict:
    messages = [SystemMessage(content=SYSTEM_PROMPT), *state["messages"]]
    response = llm.invoke(messages)
    answer = response.content

    return {
        "answer": answer,
        "messages": [response],
        "trace": [f"generate_answer: produced {len(answer)}-char response"],
    }
