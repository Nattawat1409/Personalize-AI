"""File-backed personal memory, one directory per user.

    <USERS_ROOT>/<user_id>/
        user_profile.md        who the user is, how they like answers
        topics_index.json      router index: id/title/category/one_liner/keywords
        business_logic/*.md    one file per topic, filed by genre
        python_topic/*.md
        general/*.md
        episodic/YYYY-MM-DD.md dated log of each remembered turn
        episodic/summary.md    rolling summary, rewritten by memory_consolidation

Isolation is structural: every path is derived from a validated user_id, so no
function here can reach another user's directory. All writes are
write-temp-then-os.replace(), so a crash cannot leave a truncated index.
"""

import hashlib
import json
import os
import re
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from config.memory import (
    CATEGORIES,
    EPISODIC_DAYS,
    KEYWORDS_MAX,
    USER_ID_PATTERN,
    USERS_ROOT,
)

USER_PROFILE_TEMPLATE = """---
updated_at: null
---

## Identity
_(nothing recorded yet)_

## Preferences
_(nothing recorded yet)_

## Recurring Interests
_(nothing recorded yet)_
"""

EMPTY_SECTION = "_(nothing recorded yet)_"
EMPTY_SUMMARY = "_(nothing consolidated yet)_"

_PROFILE_SECTIONS = ("Identity", "Preferences", "Recurring Interests")


# --- small pure helpers ------------------------------------------------------


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def today_str() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=str(path.parent), prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
        os.replace(tmp_path, path)
    except BaseException:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise


def _oneline(text: object) -> str:
    """Collapse whitespace/newlines — frontmatter values must stay on one line."""
    return " ".join(str(text).split())


def _escape_headings(text: str) -> str:
    """Model answers contain markdown headings; an unescaped '### ' at a line
    start would be mistaken for a new log entry when the file is re-parsed."""
    return re.sub(r"(?m)^(#+)", r"\\\1", text)


def slugify(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower().strip()).strip("-")
    if len(slug) < 3:
        # Thai (or other non-ASCII) titles slug to nothing; a hash keeps ids
        # distinct and stable instead of collapsing every one to "topic".
        slug = "topic-" + hashlib.sha1(title.encode("utf-8")).hexdigest()[:8]
    return slug[:60].strip("-")


def unique_topic_id(index: dict, base_slug: str) -> str:
    existing = {t["id"] for t in index["topics"]}
    if base_slug not in existing:
        return base_slug
    n = 2
    while f"{base_slug}-{n}" in existing:
        n += 1
    return f"{base_slug}-{n}"


def find_topic(index: dict, topic_id: str) -> Optional[dict]:
    for t in index["topics"]:
        if t["id"] == topic_id:
            return t
    return None


def render_index_for_router(index: dict) -> str:
    """Compact topic list for the router prompt: id, genre, title, one-liner,
    and keywords (only when present, so empty ones add no prompt noise)."""
    lines = []
    for t in index["topics"]:
        lines.append(f"[{t['id']}] ({t['category']}) {t['title']}")
        lines.append(f"    {t['one_liner']}")
        kws = t.get("keywords") or []
        if kws:
            lines.append(f"    keywords: {', '.join(kws[:KEYWORDS_MAX])}")
    return "\n".join(lines) if lines else "(no topics recorded yet)"


def merge_keywords(existing: list[str], new: list[str]) -> list[str]:
    """Union, case-insensitive, order-preserving, capped. Existing first: a
    topic's established vocabulary beats terms inferred from one new turn."""
    merged: list[str] = []
    seen: set[str] = set()
    for k in [*existing, *new]:
        k = (k or "").strip()
        low = k.lower()
        if not k or low in seen:
            continue
        seen.add(low)
        merged.append(k)
        if len(merged) >= KEYWORDS_MAX:
            break
    return merged


def _parse_frontmatter(content: str) -> tuple[dict, str]:
    fm_match = re.match(r"^---\n(.*?)\n---\n", content, re.DOTALL)
    if not fm_match:
        return {}, content
    fm: dict = {}
    for line in fm_match.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            fm[k.strip()] = v.strip()
    return fm, content[fm_match.end():]


# --- topic file format ---------------------------------------------------------


def _render_topic_md(
    topic_id: str,
    title: str,
    category: str,
    one_liner: str,
    summary: str,
    log_entries: list[str],
    turn_count: int,
    created_at: str,
    updated_at: str,
) -> str:
    log_block = "\n\n".join(log_entries)
    return f"""---
id: {topic_id}
title: {_oneline(title)}
category: {category}
one_liner: {_oneline(one_liner)}
created_at: {created_at}
updated_at: {updated_at}
turn_count: {turn_count}
---

## Summary

{_escape_headings(summary)}

## Conversation Log

{log_block}
"""


def _make_log_entry(query: str, answer: str) -> str:
    return (
        f"### {_now()}\n**Q:** {_oneline(query)}\n**A (key points):**\n- "
        f"{_escape_headings(answer[:3000])}"
    )


def _split_topic_md(content: str) -> tuple[dict, str, list[str]]:
    """(frontmatter, summary text, raw log-entry blocks)."""
    fm, body = _parse_frontmatter(content)
    m = re.search(r"## Summary\n\n(.*?)\n\n## Conversation Log\n\n?(.*)", body, re.DOTALL)
    summary, log_text = (m.group(1).strip(), m.group(2).strip()) if m else ("", "")
    entries = re.split(r"\n\n(?=### )", log_text) if log_text else []
    return fm, summary, [e.strip() for e in entries if e.strip()]


def extract_topic_sections(content: str) -> tuple[str, str]:
    """(summary text, conversation log text) from a topic .md file."""
    _fm, summary, entries = _split_topic_md(content)
    return summary, "\n\n".join(entries)


# --- profile format ------------------------------------------------------------


def read_profile_section(current_content: str, section: str) -> str:
    if section not in _PROFILE_SECTIONS:
        section = "Preferences"
    _fm, body = _parse_frontmatter(current_content)
    m = re.search(rf"## {re.escape(section)}\n(.*?)(?=\n## |\Z)", body, re.DOTALL)
    return m.group(1).strip() if m else EMPTY_SECTION


def merge_profile_update(current_content: str, section: str, new_text: str) -> str:
    if section not in _PROFILE_SECTIONS:
        section = "Preferences"
    sections = {name: read_profile_section(current_content, name) for name in _PROFILE_SECTIONS}
    sections[section] = new_text.strip()
    rendered = "\n\n".join(f"## {name}\n{sections[name]}" for name in _PROFILE_SECTIONS)
    return f"---\nupdated_at: {_now()}\n---\n\n{rendered}\n"


def profile_has_content(profile_md: str) -> bool:
    """True if any profile section holds something other than the placeholder."""
    return any(
        read_profile_section(profile_md, s) not in ("", EMPTY_SECTION) for s in _PROFILE_SECTIONS
    )


# --- episodic format -------------------------------------------------------------


def read_episodic_day(path: Path) -> tuple[dict, list[str]]:
    """(frontmatter, raw entry blocks) for one daily log."""
    if not path.exists():
        return {}, []
    fm, body = _parse_frontmatter(path.read_text(encoding="utf-8"))
    body = body.strip()
    entries = re.split(r"\n\n(?=### )", body) if body else []
    return fm, [e.strip() for e in entries if e.strip()]


def entry_gist_line(entry: str) -> str:
    """One display line ("question — gist") from a daily-log entry block."""
    q = re.search(r"\*\*Q:\*\*\s*(.+)", entry)
    g = re.search(r"\*\*Gist:\*\*\s*(.+)", entry)
    q_text = q.group(1).strip() if q else ""
    g_text = g.group(1).strip() if g else ""
    return f"{q_text} — {g_text}" if g_text else q_text


# --- the per-user store ------------------------------------------------------------


def validate_user_id(user_id: str) -> str:
    if not isinstance(user_id, str) or not USER_ID_PATTERN.match(user_id):
        raise ValueError(
            f"invalid user_id {user_id!r}: must match {USER_ID_PATTERN.pattern} "
            "(it becomes a directory name)"
        )
    return user_id


class UserMemory:
    def __init__(self, user_id: str, users_root: Path | None = None):
        self.user_id = validate_user_id(user_id)
        self.users_root = Path(users_root) if users_root else USERS_ROOT
        self.root = self.users_root / self.user_id
        self.index_path = self.root / "topics_index.json"
        self.profile_path = self.root / "user_profile.md"
        self.episodic_root = self.root / "episodic"
        self.summary_path = self.episodic_root / "summary.md"

    # -- lifecycle
    def exists(self) -> bool:
        return self.root.exists()

    def reset(self) -> None:
        """Delete everything stored for this user. Leaves no state behind."""
        root = self.root.resolve()
        if self.users_root.resolve() not in root.parents:  # belt and braces
            raise RuntimeError(f"refusing to delete {root}: not inside {self.users_root}")
        if root.exists():
            shutil.rmtree(root)

    # -- topics_index.json
    def load_index(self) -> dict:
        if not self.index_path.exists() or self.index_path.stat().st_size == 0:
            return {"version": 2, "topics": []}
        return json.loads(self.index_path.read_text(encoding="utf-8"))

    def save_index(self, index: dict) -> None:
        _atomic_write(self.index_path, json.dumps(index, indent=1, ensure_ascii=False) + "\n")

    # -- user_profile.md (reading never creates a file)
    def load_profile(self) -> str:
        if not self.profile_path.exists() or self.profile_path.stat().st_size == 0:
            return USER_PROFILE_TEMPLATE
        return self.profile_path.read_text(encoding="utf-8")

    def save_profile(self, content: str) -> None:
        _atomic_write(self.profile_path, content)

    # -- topic files
    def _topic_file(self, path_str: str) -> Path:
        path = (self.root / path_str).resolve()
        if self.root.resolve() not in path.parents:
            raise ValueError(f"topic path escapes user directory: {path_str!r}")
        return path

    def read_topic(self, path_str: str) -> str:
        path = self._topic_file(path_str)
        return path.read_text(encoding="utf-8") if path.exists() else ""

    def create_topic(
        self,
        title: str,
        category: str,
        one_liner: str,
        summary: str,
        query: str,
        answer: str,
        keywords: list[str] | None = None,
    ) -> tuple[str, str]:
        if category not in CATEGORIES:
            raise ValueError(f"invalid category {category!r}, must be one of {CATEGORIES}")

        index = self.load_index()
        topic_id = unique_topic_id(index, slugify(title))
        path_str = f"{category}/{topic_id}.md"
        now = _now()
        keywords = merge_keywords([], keywords or [])

        _atomic_write(
            self._topic_file(path_str),
            _render_topic_md(
                topic_id=topic_id,
                title=title,
                category=category,
                one_liner=one_liner,
                summary=summary,
                log_entries=[_make_log_entry(query, answer)],
                turn_count=1,
                created_at=now,
                updated_at=now,
            ),
        )
        index["topics"].append(
            {
                "id": topic_id,
                "title": _oneline(title),
                "category": category,
                "path": path_str,
                "one_liner": _oneline(one_liner),
                "keywords": keywords,
                "created_at": now,
                "updated_at": now,
                "turn_count": 1,
            }
        )
        self.save_index(index)
        return topic_id, path_str

    def append_topic(
        self,
        path_str: str,
        query: str,
        answer: str,
        compress_at_chars: int,
        llm_compress,
        keywords: list[str] | None = None,
    ) -> dict:
        """llm_compress(full_text) -> (summary, one_liner) runs only when the
        file already exceeds compress_at_chars."""
        path = self._topic_file(path_str)
        content = path.read_text(encoding="utf-8")
        fm, summary, entries = _split_topic_md(content)

        entries.append(_make_log_entry(query, answer))
        turn_count = int(fm.get("turn_count", len(entries))) + 1
        now = _now()

        compressed = False
        one_liner = fm.get("one_liner", "")
        if len(content) > compress_at_chars:
            summary, one_liner = llm_compress(content)
            entries = entries[-3:]
            compressed = True

        _atomic_write(
            path,
            _render_topic_md(
                topic_id=fm.get("id", ""),
                title=fm.get("title", ""),
                category=fm.get("category", ""),
                one_liner=one_liner,
                summary=summary,
                log_entries=entries,
                turn_count=turn_count,
                created_at=fm.get("created_at", now),
                updated_at=now,
            ),
        )

        index = self.load_index()
        entry = find_topic(index, fm.get("id", ""))
        merged_keywords = None
        if entry is not None:
            entry["updated_at"] = now
            entry["turn_count"] = turn_count
            if keywords:
                merged_keywords = merge_keywords(entry.get("keywords", []), keywords)
                entry["keywords"] = merged_keywords
            if compressed:
                entry["one_liner"] = _oneline(one_liner)
            self.save_index(index)

        return {
            "compressed": compressed,
            "turn_count": turn_count,
            "one_liner": one_liner,
            "keywords": merged_keywords,
        }

    # -- episodic layer
    def list_episodic_day_files(self) -> list[Path]:
        if not self.episodic_root.exists():
            return []
        return sorted(p for p in self.episodic_root.glob("*.md") if p.stem != "summary")

    def append_episodic_entry(self, query: str, gist: str, category: str) -> str:
        """Append one entry to today's log. Returns the path relative to the
        user directory, e.g. "episodic/2026-09-21.md"."""
        day = today_str()
        path = self.episodic_root / f"{day}.md"
        fm, entries = read_episodic_day(path)

        time_str = datetime.now(timezone.utc).strftime("%H:%M")
        entries.append(
            f"### {time_str} — {category}\n**Q:** {_oneline(query)}\n**Gist:** {_oneline(gist)}"
        )
        turn_count = int(fm.get("turn_count", len(entries) - 1)) + 1
        body = "\n\n".join(entries)
        _atomic_write(path, f"---\ndate: {day}\nturn_count: {turn_count}\n---\n\n{body}\n")
        return f"episodic/{day}.md"

    def load_episodic_summary(self) -> str:
        if not self.summary_path.exists() or self.summary_path.stat().st_size == 0:
            return ""
        return self.summary_path.read_text(encoding="utf-8")

    def save_episodic_summary(self, content: str) -> None:
        _atomic_write(self.summary_path, content)

    def load_episodic_context(self, days: int = EPISODIC_DAYS) -> tuple[str, list[str]]:
        """Rolling summary + the last `days` daily logs.

        Returns (text, paths_used). Days with no file simply contribute nothing.
        """
        parts: list[str] = []
        used: list[str] = []

        summary_raw = self.load_episodic_summary()
        if summary_raw:
            m = re.search(r"## Global Summary\n(.*?)\Z", summary_raw, re.DOTALL)
            summary_text = (m.group(1).strip() if m else "").strip()
            if summary_text and summary_text != EMPTY_SUMMARY:
                parts.append(f"**Summary of earlier activity:**\n{summary_text}")
                used.append("episodic/summary.md")

        day_files = self.list_episodic_day_files()
        for path in day_files[-days:] if days > 0 else day_files:
            fm, entries = read_episodic_day(path)
            if not entries:
                continue
            parts.append(
                f"**{fm.get('date', path.stem)}:**\n"
                + "\n".join(f"- {entry_gist_line(e)}" for e in entries)
            )
            used.append(f"episodic/{path.name}")

        return "\n\n".join(parts), used
