"""Build manifest.json for the mock KM corpus.

content_hash is computed from the real file bytes, so editing a document and
re-running this script produces a genuinely different hash — which is what the
incremental-ingestion test needs. doc_uid is assigned once and stays stable.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# doc_uid is assigned at first ingest and never changes, even if the file is
# edited or renamed. See docs/ARCHITECTURE.md §5.1
DOCS = [
    # path,                                          doc_uid,   title,                          version,   effective,    dept,                 category,          superseded_by
    ("production/cement-mix-spec.md",                "km-1001", "Cement Mix Spec",              "2023-R2", "2023-06-01", "Production",          "business_logic", None),
    ("rnd/cement-mix-spec.md",                       "km-1002", "Cement Mix Spec",              "2025-R1", "2025-02-15", "R&D",                 "business_logic", None),
    ("production/safety-guidelines.md",              "km-1003", "Safety Guidelines",            "2024-R1", "2024-01-10", "Plant Operations",    "general",        None),
    ("lab/safety-guidelines.md",                     "km-1004", "Safety Guidelines",            "2024-R2", "2024-05-20", "Laboratory",          "general",        None),
    ("production/concrete-mix-ratio-standard-2020.md","km-1005", "Concrete Mix Ratio Standard", "2020-R1", "2020-03-01", "Production",          "business_logic", "km-1006"),
    ("production/concrete-mix-ratio-standard-2024.md","km-1006", "Concrete Mix Ratio Standard", "2024-R3", "2024-11-01", "Production",          "business_logic", None),
    ("production/clinker-production-process.md",     "km-1007", "Clinker Production Process",   "2023-R1", "2023-09-01", "Production",          "business_logic", None),
    ("corporate/scg-business-units.md",              "km-1008", "Business Unit Overview",       "2024-R1", "2024-04-01", "Corporate",           "business_logic", None),
    ("packaging/packaging-materials-spec.md",        "km-1009", "Packaging Materials Spec",     "2024-R2", "2024-07-15", "Packaging",           "business_logic", None),
    ("engineering/python-coding-standards.md",       "km-1010", "Python Coding Standards",      "2025-R1", "2025-01-05", "Engineering",         "python_topic",   None),
    ("engineering/data-pipeline-error-handling.md",  "km-1011", "Data Pipeline Error Handling", "2024-R1", "2024-08-01", "Engineering",         "python_topic",   None),
    ("corporate/office-locations.md",                "km-1012", "Office and Site Locations",    "2025-R1", "2025-03-01", "Corporate Facilities","general",        None),
    ("it/helpdesk-faq.md",                           "km-1013", "IT Helpdesk FAQ",              "2024-R4", "2024-12-01", "IT",                  "general",        None),
]


def main() -> None:
    docs = []
    for path, uid, title, version, effective, dept, category, superseded in DOCS:
        raw = (ROOT / path).read_bytes()
        docs.append({
            "doc_uid": uid,
            "content_hash": "sha256:" + hashlib.sha256(raw).hexdigest(),
            "source_path": f"mock_km/{path}",
            "title": title,
            "version": version,
            "effective_date": effective,
            "department": dept,
            "category": category,
            "superseded_by": superseded,
            "last_accessed": None,
            "access_count": 0,
            "freshness_score": 1.0,
            "bytes": len(raw),
        })

    (ROOT / "manifest.json").write_text(
        json.dumps({"version": 1, "documents": docs}, indent=1, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    # Report the collisions this corpus deliberately contains.
    from collections import defaultdict
    by_title, by_name = defaultdict(list), defaultdict(list)
    for d in docs:
        by_title[d["title"]].append(d["doc_uid"])
        by_name[Path(d["source_path"]).name].append(d["doc_uid"])

    print(f"{len(docs)} documents indexed\n")
    print("Title collisions (same title, different content):")
    for t, uids in by_title.items():
        if len(uids) > 1:
            print(f"  {t!r}: {uids}")
    print("\nFilename collisions (same basename, different folders):")
    for n, uids in by_name.items():
        if len(uids) > 1:
            print(f"  {n}: {uids}")
    print("\nSuperseded chains:")
    for d in docs:
        if d["superseded_by"]:
            print(f"  {d['doc_uid']} ({d['version']}) -> {d['superseded_by']}")
    print("\nBy category:")
    cats = defaultdict(int)
    for d in docs:
        cats[d["category"]] += 1
    for c, n in sorted(cats.items()):
        print(f"  {c}: {n}")


if __name__ == "__main__":
    main()
