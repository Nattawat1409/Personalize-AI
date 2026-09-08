"""Nightly consolidation job — Zone 4 of the v2 diagram.

NOT a graph node: this does not run per chat turn. Run it once a day
(cron / scheduled task) via:

    uv run python -m app.jobs.nightly_consolidate

Diagram boxes implemented here:
  "Daily summary" -> "Global summary (episodic/summary.md)"
      -> "Aggregate -> user_profile.md (inferred)"

See docs/PLAN-v2.md for seeing this specific spec.
"""

import re
from collections import defaultdict
from datetime import datetime, timedelta, timezone

from pydantic import BaseModel, Field

from app.config import RECURRING_INTEREST_MIN_OCCURRENCES, RECURRING_INTEREST_WINDOW_DAYS
from app.llm import llm
from app.memory.store import (
    entry_gist_line,
    list_episodic_day_files,
    load_episodic_summary,
    load_profile,
    merge_profile_update,
    read_episodic_day,
    save_episodic_summary,
    save_profile,
)

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
with them. Write it so it stands alone, without needing the raw log.

--- Day's entries ---
{entries}
"""

MERGE_SUMMARY_PROMPT = """You maintain a rolling summary of a user's activity
over time. Combine the existing summary with the new daily digests below into
one updated summary. Keep it concise (aim for under 200 words) — compress or
drop detail that is no longer the most relevant, but keep anything a future
conversation would benefit from remembering.

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


def _parse_date(fm_date: str) -> datetime:
    return datetime.strptime(fm_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)


def consolidate_summary() -> dict:
    """Daily summary -> Global summary. Returns a small report dict."""
    day_files = list_episodic_day_files()

    summary_raw = load_episodic_summary()
    consolidated_through = None
    if summary_raw:
        for line in summary_raw.splitlines():
            if line.startswith("consolidated_through:"):
                val = line.split(":", 1)[1].strip()
                consolidated_through = None if val == "null" else val

    pending = [
        p for p in day_files
        if not consolidated_through or p.stem > consolidated_through
    ]
    # Never consolidate today's file — it may still be in progress.
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    pending = [p for p in pending if p.stem < today]

    if not pending:
        return {"digested_days": 0, "summary_updated": False}

    digests = []
    for path in pending:
        fm, entries = read_episodic_day(path)
        if not entries:
            continue
        entries_text = "\n".join(entry_gist_line(e) for e in entries)
        digest = llm.with_structured_output(DailyDigest).invoke(
            DIGEST_PROMPT.format(entries=entries_text)
        )
        digests.append(f"{fm.get('date', path.stem)}: {digest.digest}")

    if not digests:
        return {"digested_days": 0, "summary_updated": False}

    existing_summary = ""
    if summary_raw:
        m = re.search(r"## Global Summary\n(.*?)\Z", summary_raw, re.DOTALL)
        existing_summary = (m.group(1).strip() if m else "")
        if existing_summary == "_(nothing consolidated yet)_":
            existing_summary = ""

    if existing_summary:
        merged = llm.with_structured_output(MergedSummary).invoke(
            MERGE_SUMMARY_PROMPT.format(
                existing=existing_summary, new_digests="\n".join(digests)
            )
        )
        new_summary_text = merged.summary
    else:
        new_summary_text = "\n".join(digests)

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    latest_day = pending[-1].stem
    new_content = (
        f"---\nupdated_at: {now}\nconsolidated_through: {latest_day}\n---\n\n"
        f"## Global Summary\n{new_summary_text}\n"
    )
    save_episodic_summary(new_content)

    return {"digested_days": len(pending), "summary_updated": True}


def aggregate_recurring_interests() -> dict:
    """Global summary/logs -> user_profile.md Recurring Interests (inferred)."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=RECURRING_INTEREST_WINDOW_DAYS)

    lines_by_date: dict[str, list[str]] = defaultdict(list)
    for path in list_episodic_day_files():
        fm, entries = read_episodic_day(path)
        date_str = fm.get("date", path.stem)
        try:
            if _parse_date(date_str) < cutoff:
                continue
        except ValueError:
            continue
        for e in entries:
            lines_by_date[date_str].append(entry_gist_line(e))

    if not lines_by_date:
        return {"themes_found": 0, "themes_written": 0}

    entries_text = "\n".join(
        f"{d}: {line}" for d in sorted(lines_by_date) for line in lines_by_date[d]
    )

    result = llm.with_structured_output(RecurringThemes).invoke(
        THEME_PROMPT.format(window=RECURRING_INTEREST_WINDOW_DAYS, entries=entries_text)
    )

    # Code-side guard: never trust the model's claimed dates without checking
    # them against the actual log — this is what stops a single mention from
    # being written up as a "recurring" interest.
    valid_lines = []
    for theme in result.themes:
        distinct_dates = {d for d in theme.dates if d in lines_by_date}
        if len(distinct_dates) >= RECURRING_INTEREST_MIN_OCCURRENCES:
            count = len(distinct_dates)
            valid_lines.append(f"- {theme.note} ({count} times across {count} days) (inferred)")

    if not valid_lines:
        return {"themes_found": len(result.themes), "themes_written": 0}

    profile = load_profile()
    new_content = merge_profile_update(
        profile, section="Recurring Interests", new_text="\n".join(valid_lines)
    )
    save_profile(new_content)

    return {"themes_found": len(result.themes), "themes_written": len(valid_lines)}


def main() -> None:
    print("Nightly consolidation — starting")

    summary_report = consolidate_summary()
    print(
        f"  Daily -> Global summary: digested {summary_report['digested_days']} day(s), "
        f"summary.md {'updated' if summary_report['summary_updated'] else 'unchanged'}"
    )

    interest_report = aggregate_recurring_interests()
    print(
        f"  Recurring Interests: {interest_report['themes_found']} candidate(s) proposed, "
        f"{interest_report['themes_written']} met the "
        f"{RECURRING_INTEREST_MIN_OCCURRENCES}-day threshold and were written"
    )

    print("Nightly consolidation — done")


if __name__ == "__main__":
    main()
