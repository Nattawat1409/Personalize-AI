from app.memory.store import extract_topic_sections
from app.models.states.state import State


def assemble_content(state: State) -> dict:
    parts = []

    profile = state.get("user_profile", "").strip()
    if profile:
        parts.append(f"# What you know about this user\n\n{profile}")

    topic_content = state.get("topic_content", "").strip()
    if topic_content:
        summary, log_text = extract_topic_sections(topic_content)
        if summary and summary != "_(nothing recorded yet)_":
            parts.append(f"# Your notes from previous conversations on this topic\n\n{summary}")
        elif log_text:
            parts.append(f"# Your notes from previous conversations on this topic\n\n{log_text}")

    query = state["query"]
    parts.append(f"# Current question\n\n{query}")

    context = "\n\n---\n\n".join(parts)

    return {
        "context": context,
        "messages": [{"role": "user", "content": context}],
        "trace": [f"assemble_content: built context from {len(parts) - 1} memory block(s) + query"],
    }
