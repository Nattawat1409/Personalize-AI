from app.llm import llm
from app.memory.store import load_profile, merge_profile_update, read_profile_section, save_profile
from app.models.states.state import State

MERGE_PROMPT = """The user's profile has a "Preferences" section with what we
already know:

{existing}

A new fact/preference was just learned: "{new_fact}"

Rewrite the section combining both, as a short bullet list. Keep it concise —
drop anything the new fact supersedes, don't repeat yourself. Return only the
bullet list, nothing else.
"""


def update_UserProfile(state: State) -> dict:
    update_text = state.get("profile_update", "").strip()
    if not update_text:
        return {"trace": ["update_UserProfile: no profile_update text, skipped"]}

    current = load_profile()
    existing = read_profile_section(current, "Preferences")

    if existing == "_(nothing recorded yet)_":
        merged = f"- {update_text}"
    else:
        response = llm.invoke(MERGE_PROMPT.format(existing=existing, new_fact=update_text))
        merged = response.content.strip()

    new_content = merge_profile_update(current, section="Preferences", new_text=merged)
    save_profile(new_content)

    return {"trace": [f"update_UserProfile: merged '{update_text[:60]}' into Preferences"]}
