"""KM chunk schema — the shape of one entry in the KM index.

Field set matches mock_km/manifest.json exactly (see docs/ARCHITECTURE.md §5.1
for why doc_uid and content_hash are separate fields, never one). This will be
finalised in Phase 4; for now it mirrors what the mock corpus already
provides, since Phase 1 is only about separating the stores, not building the
real ingestion pipeline (Phase 3) or classification (also Phase 3).
"""

from typing import Literal, Optional

from pydantic import BaseModel

Category = Literal["business_logic", "python_topic", "general"]


class KMChunk(BaseModel):
    doc_uid: str  # stable identity — survives edits, never the filename
    content_hash: str  # sha256 of content — changes on every edit
    chunk_id: str  # f"{doc_uid}#{n:03d}"; whole-document chunks for now
    source_path: str
    title: str
    version: Optional[str] = None
    effective_date: Optional[str] = None
    department: Optional[str] = None
    category: Category
    superseded_by: Optional[str] = None
    last_accessed: Optional[str] = None
    access_count: int = 0
    freshness_score: float = 1.0
    text: str
