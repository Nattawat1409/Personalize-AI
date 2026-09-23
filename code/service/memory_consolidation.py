"""Nightly consolidation — daily log -> rolling summary -> inferred profile lines.

Diagram zone: "NIGHTLY". Not part of answering a question; it runs once a day
(or on demand at a session boundary via memory_service.end_session, so the
benchmark need not wait for a real night).

    UserMemory.list_episodic_day_files()  ->  digest per day  ->  episodic/summary.md
    recent daily logs                     ->  recurring themes ->  user_profile.md
                                                                   "Recurring Interests" (inferred)

Two guards worth knowing:
- A day is only folded into the summary once it is over. An on-demand run
  (include_today=True) digests today too but does NOT mark today as done, so
  turns logged later the same day are still picked up by the next run.
- A theme reaches the profile only if it recurs on >= RECURRING_INTEREST_MIN_OCCURRENCES
  DISTINCT days. The model proposes themes and dates; the code re-checks the
  dates against the real logs, so one mention can never become an "interest".
"""

import re
from collections import defaultdict
from datetime import datetime, timedelta, timezone

from pydantic import BaseModel, Field

from config.memory import RECURRING_INTEREST_MIN_OCCURRENCES, RECURRING_INTEREST_WINDOW_DAYS
from repository.memory_repository import (
    EMPTY_SUMMARY,
    UserMemory,
    entry_gist_line,
    merge_profile_update,
    read_episodic_day,
    today_str,
)
from tools.memory.llm import get_memory_llm


class DailyDigest(BaseModel):
    digest: str = Field(description="2-4 sentences summarising this single day's conversations.")


class MergedSummary(BaseModel):
    summary: str = Field(
        description="The rewritten global summary combining the old one with the new daily digests."
    )


class RecurringTheme(BaseModel):
    theme: str = Field(description="Short name for the recurring subject, e.g. 'cement production'.")
    dates: list[str] = Field(description="Every distinct YYYY-MM-DD date this theme appeared on.")
    note: str = Field(description="One short clause describing the interest, for display in the profile.")


class RecurringThemes(BaseModel):
    themes: list[RecurringTheme] = Field(default_factory=list)


DIGEST_PROMPT = """Summarise this single day's conversation log in 2-4 sentences.
Focus on what subjects came up and anything notable about how the user engaged
with them. Write it so it stands alone, without needing the raw log. Write in
the same language as the log entries.

--- Day's entries ---
{entries}
"""

MERGE_SUMMARY_PROMPT = """You maintain a rolling summary of a user's activity
over time. Combine the existing summary with the new daily digests below into
one updated summary. Keep it concise (aim for under 200 words) — compress or
drop detail that is no longer the most relevant, but keep anything a future
conversation would benefit from remembering. Write in the same language as the
digests.

--- Existing summary ---
{existing}

--- New daily digests ---
{new_digests}
"""

THEME_PROMPT = """Below is a list of (date, category, question — gist) entries
from a user's activity log over the last {window} days. Identify any SUBJECT
that recurs across MULTIPLE DISTINCT DAYS (not just multiple times in one day).
For each candidate, list every distinct date it appeared on — be exact, this
will be checked against the log.

Only propose a theme if you can honestly cite at least 2 distinct dates for
it; if nothing recurs across days, return an empty list. Do not invent dates.

--- Entries ---
{entries}
"""


def _parse_date(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%d").replace(tzinfo=timezone.utc)


def _consolidated_through(summary_raw: str) -> str | None:
    for line in summary_raw.splitlines():
        if line.startswith("consolidated_through:"):
            val = line.split(":", 1)[1].strip()
            return None if val in ("", "null") else val
    return None


def consolidate_summary(mem: UserMemory, include_today: bool = False) -> dict:
    """Daily digests -> rolling global summary."""
    summary_raw = mem.load_episodic_summary()
    through = _consolidated_through(summary_raw) if summary_raw else None
    today = today_str()

    pending = [
        p
        for p in mem.list_episodic_day_files()
        if (not through or p.stem > through) and (include_today or p.stem < today)
    ]

    digests = []
    for path in pending:
        fm, entries = read_episodic_day(path)
        if not entries:
            continue
        digest = get_memory_llm().with_structured_output(DailyDigest).invoke(
            DIGEST_PROMPT.format(entries="\n".join(entry_gist_line(e) for e in entries))
        )
        digests.append(f"{fm.get('date', path.stem)}: {digest.digest}")

    if not digests:
        return {"digested_days": 0, "summary_updated": False}

    existing = ""
    if summary_raw:
        m = re.search(r"## Global Summary\n(.*?)\Z", summary_raw, re.DOTALL)
        existing = (m.group(1).strip() if m else "").strip()
        if existing == EMPTY_SUMMARY:
            existing = ""

    if existing:
        merged = get_memory_llm().with_structured_output(MergedSummary).invoke(
            MERGE_SUMMARY_PROMPT.format(existing=existing, new_digests="\n".join(digests))
        )
        new_text = merged.summary
    else:
        new_text = "\n".join(digests)

    closed = [p for p in pending if p.stem < today]
    new_through = closed[-1].stem if closed else through
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    mem.save_episodic_summary(
        f"---\nupdated_at: {now}\nconsolidated_through: {new_through or 'null'}\n---\n\n"
        f"## Global Summary\n{new_text}\n"
    )
    return {"digested_days": len(digests), "summary_updated": True}


def aggregate_recurring_interests(mem: UserMemory) -> dict:
    """Recent daily logs -> profile "Recurring Interests", tagged (inferred)."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=RECURRING_INTEREST_WINDOW_DAYS)

    lines_by_date: dict[str, list[str]] = defaultdict(list)
    for path in mem.list_episodic_day_files():
        fm, entries = read_episodic_day(path)
        date_str = fm.get("date", path.stem)
        try:
            if _parse_date(date_str) < cutoff:
                continue
        except ValueError:
            continue
        lines_by_date[date_str].extend(entry_gist_line(e) for e in entries)

    if not lines_by_date:
        return {"themes_found": 0, "themes_written": 0}

    entries_text = "\n".join(f"{d}: {line}" for d in sorted(lines_by_date) for line in lines_by_date[d])
    result = get_memory_llm().with_structured_output(RecurringThemes).invoke(
        THEME_PROMPT.format(window=RECURRING_INTEREST_WINDOW_DAYS, entries=entries_text)
    )

    valid_lines = []
    for theme in result.themes:
        distinct = {d for d in theme.dates if d in lines_by_date}
        if len(distinct) >= RECURRING_INTEREST_MIN_OCCURRENCES:
            valid_lines.append(
                f"- {theme.note} ({len(distinct)} times across {len(distinct)} days) (inferred)"
            )

    if not valid_lines:
        return {"themes_found": len(result.themes), "themes_written": 0}

    mem.save_profile(
        merge_profile_update(
            mem.load_profile(), section="Recurring Interests", new_text="\n".join(valid_lines)
        )
    )
    return {"themes_found": len(result.themes), "themes_written": len(valid_lines)}


def consolidate(user_id: str, include_today: bool = False) -> dict:
    mem = UserMemory(user_id)
    return {
        **consolidate_summary(mem, include_today=include_today),
        **aggregate_recurring_interests(mem),
    }
