```mermaid
flowchart TD
    start([User Query]) -->|load from current content| profile[Load user_profile.md]
    start --> t1{Search topics_index}
    
    t1 -->|Match found| read[Read specific topic .md]
    t1 -->|No match| nocxt[No prior topic context]
    
    profile --> ctx[Assemble Context]
    read --> ctx
    nocxt --> ctx
    
    ctx --> gen[Generate Answer]
    gen --> out([Output to User])
    
    %% Synchronous ReAct Check (Lock User Input)
    out --> t3{Worth remembering?}
    
    t3 -->|No| finish([End / Unlock User Input])
    t3 -->|Existing Topic| append[Append/Compress topic .md]
    t3 -->|New Topic| create[Create .md & Update topics_index]
    t3 -->|User Preference Only| update_prof[Update user_profile.md]
    
    append --> finish
    create --> finish
    update_prof --> finish
```

## Memory layout

```
memory/
  topics_index.json          # topic -> {file, category, keywords/embedding}
  user_profile.md            # MD1 — single file, always loaded
  business_logic/
    *.md                     # MD2 — one file per strategy/business-logic topic
  knowledge/
    *.md                     # MD3 — one file per subject/technique topic
```

`topics_index.json` is what `search_memory` checks first — it's the router, so the
agent never has to open every `.md` file to find out what already exists. Each
topic file gets appended/updated in place when the same topic recurs, and
compacted (summarized) once it grows past a size threshold, rather than
growing unbounded.