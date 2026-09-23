"""Memory WRITE — record a stable fact/preference the user stated about themself.
Diagram box: "Update user_profile.md". Facts the user says outright are tagged
(direct); ones inferred by the nightly job are tagged (inferred)."""

from repository.memory_repository import (
    EMPTY_SECTION,
    UserMemory,
    merge_profile_update,
    read_profile_section,
)
from tools.memory.llm import get_memory_llm
from workflow.state import State

MERGE_PROMPT = """The user's profile has a "Preferences" section with what we
already know:

{existing}

A new fact/preference was just learned: "{new_fact}"

Rewrite the section combining both, as a short bullet list. Keep it concise —
drop anything the new fact supersedes, don't repeat yourself. Preserve the
"(direct)" or "(inferred)" tag already on each existing line. Append the tag
"(direct)" to the new fact's line — it was explicitly stated by the user, not
inferred. Return only the bullet list, nothing else.
"""


def update_UserProfile(state: State) -> dict:
    update_text = (state.get("profile_update") or "").strip()
    if not update_text:
        return {"trace": ["update_UserProfile: no profile_update text, skipped"]}

    mem = UserMemory(state["user_id"])
    current = mem.load_profile()
    existing = read_profile_section(current, "Preferences")

    if existing == EMPTY_SECTION:
        merged = f"- {update_text} (direct)"
    else:
        response = get_memory_llm().invoke(
            MERGE_PROMPT.format(existing=existing, new_fact=update_text)
        )
        content = response.content
        merged = (content if isinstance(content, str) else str(content)).strip()

    mem.save_profile(merge_profile_update(current, section="Preferences", new_text=merged))
    return {"trace": [f"update_UserProfile: merged '{update_text[:60]}' into Preferences"]}
