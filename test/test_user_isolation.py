"""User isolation is a tested property (docs/HANDOFF_NEW_ARCHITECTURE.md §6, §9):
one user's memory must never appear in an answer for another.

These tests need no network and no LLM: a user with no topics never triggers the
router call, so read_memory() is fully deterministic for them. Memory is written
straight through the repository into a throwaway directory.

    uv run python test/test_user_isolation.py
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path

# Point memory at a throwaway directory BEFORE any memory module is imported —
# config.memory reads this env var at import time, so real data is never touched.
_TMP = tempfile.mkdtemp(prefix="personalize_iso_")
os.environ["PERSONALIZE_MEMORY_ROOT"] = _TMP
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "code"))

from repository.memory_repository import (  # noqa: E402
    USER_PROFILE_TEMPLATE,
    UserMemory,
    merge_profile_update,
)
from service import memory_service as memory  # noqa: E402

SECRET_A = "ALICE-SECRET-4711"
SECRET_B = "BOB-SECRET-9032"


def seed(user_id: str, secret: str) -> UserMemory:
    """A user with a profile fact and an episodic entry, but no topics."""
    mem = UserMemory(user_id)
    mem.save_profile(
        merge_profile_update(USER_PROFILE_TEMPLATE, "Preferences", f"- likes {secret} (direct)")
    )
    mem.append_episodic_entry(query=f"asked about {secret}", gist=f"discussed {secret}", category="general")
    return mem


class UserIsolation(unittest.TestCase):
    def setUp(self):
        for uid in ("alice", "bob", "carol"):
            UserMemory(uid).reset()

    # --- the property itself -------------------------------------------------
    def test_one_users_memory_never_reaches_another(self):
        seed("alice", SECRET_A)
        seed("bob", SECRET_B)

        a = memory.read_memory("alice", "anything")
        b = memory.read_memory("bob", "anything")

        # sanity: memory really is injected for its owner (else the negatives prove nothing)
        self.assertIn(SECRET_A, a.block)
        self.assertIn(SECRET_B, b.block)
        # ...and never for anyone else
        self.assertNotIn(SECRET_B, a.block)
        self.assertNotIn(SECRET_A, b.block)

    def test_user_with_no_memory_gets_no_memory_block(self):
        seed("alice", SECRET_A)
        c = memory.read_memory("carol", f"tell me about {SECRET_A}")  # asks for Alice's secret by name
        self.assertEqual(c.block, "")
        self.assertEqual(c.used, [])
        self.assertIsNone(c.error)

    def test_topic_files_are_per_user(self):
        alice = UserMemory("alice")
        _id, path = alice.create_topic(
            title="alice private topic",
            category="general",
            one_liner=SECRET_A,
            summary=SECRET_A,
            query=SECRET_A,
            answer=SECRET_A,
            keywords=[SECRET_A],
        )
        bob = UserMemory("bob")
        self.assertEqual(bob.load_index()["topics"], [])
        self.assertEqual(bob.read_topic(path), "")  # same relative path, Bob's own (empty) directory
        self.assertIn(SECRET_A, alice.read_topic(path))

    def test_path_traversal_between_users_is_refused(self):
        seed("alice", SECRET_A)
        _id, path = UserMemory("alice").create_topic(
            title="t", category="general", one_liner="x", summary="x", query="x", answer="x"
        )
        with self.assertRaises(ValueError):
            UserMemory("bob").read_topic(f"../alice/{path}")

    # --- user_id becomes a directory name: it must be safe -----------------------
    def test_unsafe_user_ids_are_rejected(self):
        for bad in ("../alice", "a/b", "", ".hidden", "x" * 65, "a b", "..", "/etc"):
            with self.subTest(user_id=bad):
                with self.assertRaises(ValueError):
                    UserMemory(bad)

    # --- reset_memory: leaves no state behind --------------------------------------
    def test_reset_removes_everything_for_that_user_only(self):
        alice, bob = seed("alice", SECRET_A), seed("bob", SECRET_B)
        self.assertTrue(alice.exists())

        memory.reset_memory("alice")

        self.assertFalse(alice.exists())
        self.assertEqual(memory.read_memory("alice", "x").block, "")
        self.assertTrue(bob.exists())  # Bob untouched
        self.assertIn(SECRET_B, memory.read_memory("bob", "x").block)

    def test_reset_of_unknown_user_is_a_noop(self):
        memory.reset_memory("carol")  # never existed: must not raise

    # --- baseline parity: nothing to inject means exactly the baseline prompt ------
    def test_empty_or_placeholder_memory_injects_nothing(self):
        self.assertEqual(memory.build_memory_block({}), ("", []))
        self.assertEqual(memory.build_memory_block({"user_profile": USER_PROFILE_TEMPLATE}), ("", []))

    def test_kill_switch_parsing(self):
        for value, expected in (("false", False), ("0", False), ("OFF", False), ("no", False),
                                ("true", True), ("1", True), ("", True)):
            with self.subTest(value=value):
                os.environ["MEMORY_ENABLED"] = value
                self.assertEqual(memory.memory_enabled(), expected)
        os.environ.pop("MEMORY_ENABLED", None)
        self.assertTrue(memory.memory_enabled())  # default on


if __name__ == "__main__":
    unittest.main(verbosity=2)
