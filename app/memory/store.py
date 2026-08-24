import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from app.config import CATEGORIES, MEMORY_ROOT, TOPICS_INDEX_PATH, USER_PROFILE_PATH

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


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


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


# --- topics_index.json ---------------------------------------------------

def load_index() -> dict:
    if not TOPICS_INDEX_PATH.exists() or TOPICS_INDEX_PATH.stat().st_size == 0:
        return {"version": 2, "topics": []}
    return json.loads(TOPICS_INDEX_PATH.read_text(encoding="utf-8"))


def save_index(index: dict) -> None:
    _atomic_write(TOPICS_INDEX_PATH, json.dumps(index, indent=2, ensure_ascii=False) + "\n")


def find_topic(index: dict, topic_id: str) -> Optional[dict]:
    for t in index["topics"]:
        if t["id"] == topic_id:
            return t
    return None


def render_index_for_router(index: dict) -> str:
    lines = []
    for t in index["topics"]:
        lines.append(f"[{t['id']}] ({t['category']}) {t['title']}")
        lines.append(f"    {t['one_liner']}")
    return "\n".join(lines) if lines else "(no topics recorded yet)"


# --- user_profile.md -------------------------------------------------------

def load_profile() -> str:
    if not USER_PROFILE_PATH.exists() or USER_PROFILE_PATH.stat().st_size == 0:
        _atomic_write(USER_PROFILE_PATH, USER_PROFILE_TEMPLATE)
        return USER_PROFILE_TEMPLATE
    return USER_PROFILE_PATH.read_text(encoding="utf-8")


def save_profile(content: str) -> None:
    _atomic_write(USER_PROFILE_PATH, content)


# --- slugify ---------------------------------------------------------------

def slugify(title: str) -> str:
    slug = title.lower().strip()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = slug.strip("-")
    return slug or "topic"


def unique_topic_id(index: dict, base_slug: str) -> str:
    existing_ids = {t["id"] for t in index["topics"]}
    if base_slug not in existing_ids:
        return base_slug
    n = 2
    while f"{base_slug}-{n}" in existing_ids:
        n += 1
    return f"{base_slug}-{n}"


# --- topic .md files ---------------------------------------------------------

def _topic_path(category: str, topic_id: str) -> Path:
    return MEMORY_ROOT / category / f"{topic_id}.md"


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
title: {title}
category: {category}
one_liner: {one_liner}
created_at: {created_at}
updated_at: {updated_at}
turn_count: {turn_count}
---

## Summary

{summary}

## Conversation Log

{log_block}
"""


def _make_log_entry(query: str, answer: str) -> str:
    return f"### {_now()}\n**Q:** {query}\n**A (key points):**\n- {answer}"


def extract_topic_sections(content: str) -> tuple[str, str]:
    """Returns (summary_text, conversation_log_text) from a topic .md file."""
    _fm, summary, entries = _split_topic_md(content)
    log_text = "\n\n".join(entries)
    return summary, log_text


def read_topic(path_str: str) -> str:
    path = MEMORY_ROOT / path_str
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def create_topic(
    title: str,
    category: str,
    one_liner: str,
    summary: str,
    query: str,
    answer: str,
) -> tuple[str, str]:
    if category not in CATEGORIES:
        raise ValueError(f"invalid category: {category!r}, must be one of {CATEGORIES}")

    index = load_index()
    topic_id = unique_topic_id(index, slugify(title))
    path_str = f"{category}/{topic_id}.md"
    now = _now()

    content = _render_topic_md(
        topic_id=topic_id,
        title=title,
        category=category,
        one_liner=one_liner,
        summary=summary,
        log_entries=[_make_log_entry(query, answer)],
        turn_count=1,
        created_at=now,
        updated_at=now,
    )
    _atomic_write(_topic_path(category, topic_id), content)

    index["topics"].append(
        {
            "id": topic_id,
            "title": title,
            "category": category,
            "path": path_str,
            "one_liner": one_liner,
            "keywords": [],
            "created_at": now,
            "updated_at": now,
            "turn_count": 1,
        }
    )
    save_index(index)
    return topic_id, path_str


def _split_topic_md(content: str) -> tuple[dict, str, list[str]]:
    """Returns (frontmatter dict, summary text, list of raw log entry blocks)."""
    fm_match = re.match(r"^---\n(.*?)\n---\n", content, re.DOTALL)
    fm: dict = {}
    body = content
    if fm_match:
        for line in fm_match.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                fm[k.strip()] = v.strip()
        body = content[fm_match.end():]

    summary_match = re.search(r"## Summary\n\n(.*?)\n\n## Conversation Log\n\n?(.*)", body, re.DOTALL)
    if summary_match:
        summary = summary_match.group(1).strip()
        log_text = summary_match.group(2).strip()
    else:
        summary = ""
        log_text = ""

    entries = re.split(r"\n\n(?=### )", log_text) if log_text else []
    entries = [e.strip() for e in entries if e.strip()]
    return fm, summary, entries


def append_topic(path_str: str, query: str, answer: str, compress_at_chars: int, llm_compress) -> dict:
    """llm_compress(full_text) -> (new_summary, new_one_liner) is called only when
    the file exceeds compress_at_chars."""
    path = MEMORY_ROOT / path_str
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

    new_content = _render_topic_md(
        topic_id=fm.get("id", ""),
        title=fm.get("title", ""),
        category=fm.get("category", ""),
        one_liner=one_liner,
        summary=summary,
        log_entries=entries,
        turn_count=turn_count,
        created_at=fm.get("created_at", now),
        updated_at=now,
    )
    _atomic_write(path, new_content)

    index = load_index()
    entry = find_topic(index, fm.get("id", ""))
    if entry is not None:
        entry["updated_at"] = now
        entry["turn_count"] = turn_count
        if compressed:
            entry["one_liner"] = one_liner
        save_index(index)

    return {"compressed": compressed, "turn_count": turn_count, "one_liner": one_liner}


# --- user profile update ---------------------------------------------------

_SECTIONS = ("Identity", "Preferences", "Recurring Interests")


def read_profile_section(current_content: str, section: str) -> str:
    if section not in _SECTIONS:
        section = "Preferences"
    fm_match = re.match(r"^---\n(.*?)\n---\n", current_content, re.DOTALL)
    body = current_content[fm_match.end():] if fm_match else current_content
    m = re.search(rf"## {re.escape(section)}\n(.*?)(?=\n## |\Z)", body, re.DOTALL)
    return m.group(1).strip() if m else "_(nothing recorded yet)_"


def merge_profile_update(current_content: str, section: str, new_text: str) -> str:
    if section not in _SECTIONS:
        section = "Preferences"

    fm_match = re.match(r"^---\n(.*?)\n---\n", current_content, re.DOTALL)
    body = current_content[fm_match.end():] if fm_match else current_content

    sections: dict[str, str] = {}
    for name in _SECTIONS:
        m = re.search(rf"## {re.escape(name)}\n(.*?)(?=\n## |\Z)", body, re.DOTALL)
        sections[name] = m.group(1).strip() if m else "_(nothing recorded yet)_"

    sections[section] = new_text.strip()

    now = _now()
    rendered_sections = "\n\n".join(f"## {name}\n{sections[name]}" for name in _SECTIONS)
    return f"---\nupdated_at: {now}\n---\n\n{rendered_sections}\n"
