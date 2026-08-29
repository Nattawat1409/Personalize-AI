# v2 flow diagram (Cimie)

> Canonical version lives in [ARCHITECTURE.md](ARCHITECTURE.md) §4.
> This file is the standalone diagram, kept for pasting into slides.

```mermaid
flowchart TB
    subgraph OFF["OFFLINE — KM Ingestion (outside the chat graph)"]
        ev[New/updated doc in KM] --> hash{doc_id = content_hash<br/>changed?}
        night[Nightly reconciliation sweep] --> hash
        hash -->|changed| proc[Chunk + embed<br/>+ LLM classify topic<br/>+ extract metadata]
        hash -->|unchanged| skip[Skip]
        proc --> conf[Dedup / Merge /<br/>Conflict resolution]
        conf --> KMIDX[(KM Index<br/>BM25 + dense<br/>version / date / dept<br/>+ staleness decay)]
    end

    subgraph ON["ONLINE — Chat turn"]
        q([User Query]) --> prof[Load user_profile.md<br/>+ summary.md + recent episodic]
        q --> qa[Query Understanding<br/>expand + classify topic]

        qa --> hyb[Hybrid Retrieve<br/>BM25 + dense, top-20]
        KMIDX -.-> hyb
        hyb --> prune[Prune by topic taxonomy]
        prune --> rr[Cross-encoder Rerank<br/>20 to 5]

        qa --> pm{Personal topics_index<br/>LLM router, small N}
        pm -->|match| pr[Read topic .md]
        pm -->|no match| pn[No prior topic context]

        prof --> ctx[Assemble Context]
        rr --> ctx
        pr --> ctx
        pn --> ctx
        ctx --> gen[Generate Answer<br/>cite doc_id + version]
        gen --> out([Output to User])
    end

    subgraph WR["ASYNC — Memory write-back (off the critical path)"]
        out -.-> w{Worth remembering?}
        w -->|No| fin([End])
        w -->|Episodic| epi[Append dated entry<br/>episodic/YYYY-MM-DD.md]
        w -->|Topic| tp[Append / Create topic .md]
        w -->|Preference| up[Update user_profile.md — direct]
    end

    subgraph NI["NIGHTLY — Personal memory consolidation"]
        epi -.-> ds[Daily summary]
        ds --> gs[Global summary → episodic/summary.md]
        gs --> agg[Aggregate insights<br/>→ user_profile.md — inferred]
    end
```

**Note on decay:** staleness decay lives in the **KM Index only**. The nightly
personal-memory job consolidates but never forgets — see
[ARCHITECTURE.md](ARCHITECTURE.md) §7 for the reasoning.
