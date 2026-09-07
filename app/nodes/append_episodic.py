from app.memory.store import append_episodic_entry
from app.models.states.state import State


def append_episodic(state: State) -> dict:
    """Diagram box: 'Worth remembering?' -> 'Append episodic/YYYY-MM-DD.md'.

    Runs after append_md/create_md/update_UserProfile, on every turn that
    decision_worth judged worth remembering (i.e. every action except "skip").
    This is in addition to whichever of those three already ran this turn —
    the intentional v1 diagram departure documented in PLAN-v2.md §6.
    """
    gist = state.get("episodic_gist") or state.get("topic_summary") or state.get(
        "profile_update"
    ) or state["answer"][:200]
    category = state.get("episodic_category") or state.get("memory_category") or "general"

    path = append_episodic_entry(query=state["query"], gist=gist, category=category)

    return {"trace": [f"append_episodic: logged to '{path}' (category={category})"]}
