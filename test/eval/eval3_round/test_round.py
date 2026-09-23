"""Aggregate the 3 order-shuffle rounds (round1/round2/round3) into one summary.

Each round/ subfolder holds a report_*.json produced by score_benchmark.py,
scoring baseline vs personalize on the SAME 22 turns but a DIFFERENT question
order (round1 = evalset.json, round2 = evalset2.json seed 202, round3 =
evalset3.json seed 303 — see evalset2.json/evalset3.json's "note" field).

Purpose: check whether the 4 metrics are stable across question order, or
whether they are largely an artifact of the specific order the questions
happened to be asked in. A metric with a small spread across rounds is
trustworthy; a metric that swings a lot (e.g. wrong-memory rate did: 5.3% /
10.5% / 10.5% for baseline) should be reported with that caveat attached.

Usage (repo root):
    uv run python test/eval/eval3_round/test_round.py
Writes test/eval/eval3_round/3round.json and prints a summary table.
"""

import json
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent  # test/eval/eval3_round/
ROUNDS = ["round1", "round2", "round3"]

# (label, path-in-report, "higher"/"lower" is better — for display only)
METRICS = [
    ("win_rate", ("win_rate", "value"), "higher"),
    ("cross_session_recall_baseline", ("systems", "baseline", "cross_session_recall", "value"), "higher"),
    ("cross_session_recall_personalize", ("systems", "personalize", "cross_session_recall", "value"), "higher"),
    ("wrong_memory_baseline", ("systems", "baseline", "wrong_memory", "value"), "lower"),
    ("wrong_memory_personalize", ("systems", "personalize", "wrong_memory", "value"), "lower"),
    ("recall_at_8_baseline", ("systems", "baseline", "recall_at_8", "value"), "n/a (must match personalize)"),
    ("recall_at_8_personalize", ("systems", "personalize", "recall_at_8", "value"), "n/a (must match baseline)"),
]


def dig(d: dict, path: tuple):
    for key in path:
        if d is None:
            return None
        d = d.get(key)
    return d


def latest_report(round_dir: Path) -> Path:
    matches = sorted(round_dir.glob("report_*.json"))
    if not matches:
        sys.exit(f"{round_dir}: no report_*.json found — run score_benchmark.py --out-dir {round_dir} first")
    return matches[-1]  # newest, if a round was ever re-scored


def main() -> None:
    per_round = {}
    for r in ROUNDS:
        round_dir = HERE / r
        path = latest_report(round_dir)
        report = json.loads(path.read_text())
        per_round[r] = {"report_file": path.name, "values": {}}
        for label, keypath, _ in METRICS:
            per_round[r]["values"][label] = dig(report, keypath)

    summary = {}
    for label, _, better in METRICS:
        vals = [per_round[r]["values"][label] for r in ROUNDS]
        missing = [r for r, v in zip(ROUNDS, vals) if v is None]
        if missing:
            summary[label] = {"error": f"missing in {missing}", "values_by_round": dict(zip(ROUNDS, vals))}
            continue
        summary[label] = {
            "better": better,
            "values_by_round": dict(zip(ROUNDS, vals)),
            "mean": statistics.mean(vals),
            "stdev": statistics.stdev(vals) if len(vals) > 1 else 0.0,
            "min": min(vals),
            "max": max(vals),
            "spread": max(vals) - min(vals),
        }

    out = {
        "purpose": (
            "Same 22 turns, same baseline/personalize systems — only the ORDER "
            "questions were asked in differs per round (round1=evalset.json, "
            "round2=evalset2.json seed 202, round3=evalset3.json seed 303). "
            "A metric with a small spread across rounds is order-independent and "
            "trustworthy; a large spread means that metric is sensitive to "
            "question order (or to judge noise) and single-round numbers from it "
            "should not be over-trusted."
        ),
        "rounds": per_round,
        "summary": summary,
    }

    out_path = HERE / "3round.json"
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2))

    print(f"\n=== 3-ROUND SUMMARY (order-shuffle robustness check) ===\n")
    print(f"{'metric':34} {'round1':>8} {'round2':>8} {'round3':>8} {'mean':>8} {'stdev':>8} {'spread':>8}  better")
    print("-" * 100)
    for label, _, better in METRICS:
        s = summary[label]
        if "error" in s:
            print(f"{label:34} ERROR: {s['error']}")
            continue
        v = s["values_by_round"]
        print(
            f"{label:34} {v['round1']*100:7.1f}% {v['round2']*100:7.1f}% {v['round3']*100:7.1f}% "
            f"{s['mean']*100:7.1f}% {s['stdev']*100:7.1f}% {s['spread']*100:7.1f}%  {better}"
        )
    print(f"\n-> {out_path}")


if __name__ == "__main__":
    main()
