from app.memory.store import load_profile
from app.models.states.state import State


def loading_userProfiles(state: State) -> dict:
    profile = load_profile()
    return {
        "user_profile": profile,
        "trace": [f"loading_userProfiles: loaded user_profile.md ({len(profile)} chars)"],
    }
