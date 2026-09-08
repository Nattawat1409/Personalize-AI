from app.config import EPISODIC_DAYS
from app.memory.store import load_episodic_context, load_profile
from app.models.states.state import State


def loading_userProfiles(state: State) -> dict:
    profile = load_profile()
    episodic_context = load_episodic_context(days=EPISODIC_DAYS)

    trace = [f"loading_userProfiles: loaded user_profile.md ({len(profile)} chars)"]
    trace.append(
        f"loading_userProfiles: loaded episodic context ({len(episodic_context)} chars, "
        f"last {EPISODIC_DAYS} days)"
    )

    return {
        "user_profile": profile,
        "episodic_context": episodic_context,
        "trace": trace,
    }
