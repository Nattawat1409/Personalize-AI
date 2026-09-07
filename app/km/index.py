"""Build and query the KM index.

This is Phase 1 scope only: prove the KM store is genuinely SEPARATE from
`topics_index.json` and can be queried end to end. Two things are deliberately
NOT built here, because they belong to later phases:

- Retrieval quality: `query_index()` uses a naive keyword-overlap score, not
  hybrid (BM25 + dense) retrieval or a cross-encoder reranker. Those are
  Phase 2. This placeholder exists only so Phase 1's acceptance test
  ("a KM query returns KM chunks") is verifiable end to end.
- Ingestion: `build_index()` does a one-shot full rebuild from
  mock_km/manifest.json on every call. Event-driven incremental ingestion +
  nightly reconciliation is Phase 3.

Deliberately does not import anything from app.memory.store — the whole point
of Phase 1 is that this is a separate store with no path back into personal
memory.
"""

import json
import os
import re
import tempfile
from pathlib import Path

from app.config import KM_INDEX_PATH, KM_MANIFEST_PATH, KM_ROOT, KM_TOP_K
from app.km.schema import KMChunk

INDEX_FILE = KM_INDEX_PATH / "index.json"


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


def build_index() -> int:
    """Rebuilds the KM index from mock_km/manifest.json + the document files.

    Whole documents as single chunks — the mock corpus documents are short
    (~1-2KB), so real chunking logic isn't needed to prove index separation.
    Returns the number of chunks indexed.
    """
    manifest = json.loads(KM_MANIFEST_PATH.read_text(encoding="utf-8"))

    chunks: list[dict] = []
    for doc in manifest["documents"]:
        path = KM_ROOT.parent / doc["source_path"]
        text = path.read_text(encoding="utf-8")
        chunk = KMChunk(
            doc_uid=doc["doc_uid"],
            content_hash=doc["content_hash"],
            chunk_id=f"{doc['doc_uid']}#000",
            source_path=doc["source_path"],
            title=doc["title"],
            version=doc.get("version"),
            effective_date=doc.get("effective_date"),
            department=doc.get("department"),
            category=doc["category"],
            superseded_by=doc.get("superseded_by"),
            last_accessed=doc.get("last_accessed"),
            access_count=doc.get("access_count", 0),
            freshness_score=doc.get("freshness_score", 1.0),
            text=text,
        )
        chunks.append(chunk.model_dump())

    _atomic_write(INDEX_FILE, json.dumps({"version": 1, "chunks": chunks}, indent=1) + "\n")
    return len(chunks)


def load_index() -> list[dict]:
    if not INDEX_FILE.exists():
        return []
    return json.loads(INDEX_FILE.read_text(encoding="utf-8"))["chunks"]


_WORD_RE = re.compile(r"[a-z0-9]+")


def _tokenize(text: str) -> set[str]:
    return set(_WORD_RE.findall(text.lower()))


def query_index(query: str, top_k: int = KM_TOP_K, category: str | None = None) -> list[dict]:
    """Naive keyword-overlap ranking — placeholder until Phase 2's hybrid
    retrieve + reranker replace this. Do not treat this ranking as final;
    it exists only to prove the KM store is queryable and separate from
    personal memory.
    """
    chunks = load_index()
    if category:
        chunks = [c for c in chunks if c["category"] == category]

    q_tokens = _tokenize(query)
    scored = []
    for c in chunks:
        c_tokens = _tokenize(c["title"] + " " + c["text"])
        overlap = len(q_tokens & c_tokens)
        if overlap > 0:
            scored.append((overlap, c))

    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [c for _score, c in scored[:top_k]]
