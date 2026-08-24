# Purpose #
- research for AI personalize feature to optimize the operation workflow of CIMIE and memorize the user personalize and frequently question by my vary user 

# workflow #
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
