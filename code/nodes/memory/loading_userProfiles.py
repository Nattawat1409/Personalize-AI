"""Memory READ, step 1 — load the user's profile and recent episodic log.

Diagram box: "Load user_profile.md + episodic summary". Never touches retrieval.
"""

from config.memory import EPISODIC_DAYS
from repository.memory_repository import UserMemory
from workflow.state import State


def loading_userProfiles(state: State) -> dict:
    mem = UserMemory(state["user_id"])
    profile = mem.load_profile()
    episodic_context, episodic_paths = mem.load_episodic_context(days=EPISODIC_DAYS)

    return {
        "user_profile": profile,
        "episodic_context": episodic_context,
        "episodic_paths": episodic_paths,
        "trace": [
            f"loading_userProfiles: profile {len(profile)} chars, episodic "
            f"{len(episodic_context)} chars from {len(episodic_paths)} file(s)"
        ],
    }
