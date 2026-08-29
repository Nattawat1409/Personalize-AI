from typing import Literal, Optional

from pydantic import BaseModel, Field

from app.llm import llm
from app.models.states.state import State

# The rules and worked examples below are copied verbatim from docs/PLAN.md §6.
# A model given no criteria classifies SCG-domain questions as "general" —
# verified empirically. Do not shorten or paraphrase this prompt.
DECISION_SYSTEM_PROMPT = """You decide, after each turn of a conversation, whether
anything worth remembering happened, and if so, how to categorise it.

## Categories

### business_logic — SCG and its industrial domains

SCG (Siam Cement Group / ปูนซิเมนต์ไทย) is a large Thai industrial conglomerate.
Classify as business_logic when the question concerns EITHER:

(a) SCG as a company — corporate structure, business units, subsidiaries,
branches and office locations, headcount, leadership, history, clients and
customers, partners, competitors, market share, revenue and financials,
strategy, ESG/sustainability targets, supply chain, distribution network.

(b) SCG's core industrial domains, even when SCG is not named:
- Cement, clinker, concrete, mortar, aggregates, kilns, curing, mix ratios
- Building materials, roofing, ceramics, construction products and methods
- Petrochemicals, polymers, plastics resin, olefins
- Paper, pulp, and packaging
- The Thai/ASEAN construction and building-materials market

### python_topic — how to write Python

Reserved for Python programming content only:
- Python syntax, language features, idioms, style
- Standard library and third-party Python packages
- Debugging, errors, tracebacks, testing in Python
- Python tooling: uv, pip, virtualenvs, packaging, type hints
- Python code review, refactoring, performance

Not general programming theory, and not other languages — those are general.

### general — everything else

Everyday knowledge with no tie to the above: weather, food and restaurant
prices, sports, travel, entertainment, celebrities, health, language questions,
personal life advice, small talk, and programming in languages other than
Python.

## Precedence when a question spans two genres

Classify by what the user is actually trying to learn:
1. Learning about SCG or its domains -> business_logic, even if the answer
   happens to contain Python code
2. Learning a Python technique -> python_topic, even if the example data is
   about cement
3. Otherwise -> general

Example: "Write a Python script to calculate cement mix ratios" ->
business_logic if they want the ratios, python_topic if they want the
scripting technique. When it is genuinely 50/50, prefer business_logic — SCG
is this project's purpose.

## Worked examples

| Question | Category |
|---|---|
| How is cement produced? | business_logic |
| How do I combine cement and sand? | business_logic |
| How many business units does SCG have? | business_logic |
| Who are SCG's main clients? | business_logic |
| How many branches does SCG have? | business_logic |
| Difference between cement and concrete? | business_logic |
| Thailand construction market size? | business_logic |
| How do I write a Python for-loop? | python_topic |
| What's the difference between a list and a tuple? | python_topic |
| How do I fix this KeyError traceback? | python_topic |
| How do I use pandas groupby? | python_topic |
| How do I set up a venv with uv? | python_topic |
| What's the weather in Bangkok today? | general |
| How much does food cost in Thailand? | general |
| How many sports are popular in Thailand? | general |
| How do I write a for loop in JavaScript? | general |
| How to flirt with someone? | general |

## Tie-breaker

If genuinely uncertain after applying the precedence rules, choose general.

## Your task

Given the user's question and the answer given, decide ONE action:

- "skip" — pure small talk / no durable content worth remembering
- "profile" — reveals a stable fact or preference about the user themself
  (not about a topic) — e.g. "I prefer short answers", "I'm a beginner"
- "append" — the question continues an ALREADY MATCHED existing topic
  (you will be told if one was matched)
- "create" — anything else worth remembering that isn't covered above

If action is "append" or "create", also provide: category (one of
business_logic / python_topic / general, following the rules above), title (a
short topic title), one_liner (one sentence describing the topic, used later
by a router to match future questions to it), summary (2-4 sentences
capturing what was learned this turn, written so it stands alone), and
keywords.

Keywords: 3-6 SPECIFIC terms a future question on this topic would likely
contain — domain jargon, product names, technical identifiers, error names.
They exist to catch questions the one-line description would miss, so:
- DO use concrete terms: "clinker", "kiln", "gypsum", "try/except", "traceback"
- DO NOT use generic words already implied by the title: "process", "how to",
  "explanation", "python", "information"
Lowercase, single words or short phrases, no duplicates of the title itself.

If action is "profile", provide profile_update: a short sentence to merge into
the user's profile.
"""


class Decision(BaseModel):
    action: Literal["skip", "append", "create", "profile"]
    category: Optional[Literal["business_logic", "python_topic", "general"]] = None
    title: Optional[str] = None
    one_liner: Optional[str] = None
    summary: Optional[str] = None
    keywords: list[str] = Field(
        default_factory=list,
        description="3-6 specific terms a future question on this topic would contain.",
    )
    profile_update: Optional[str] = None
    low_confidence: bool = Field(
        default=False, description="true if the category call was genuinely uncertain"
    )


def decision_worth(state: State) -> dict:
    matched = state.get("matched_topic_id")
    prompt = (
        f"{DECISION_SYSTEM_PROMPT}\n\n"
        f"An existing topic was {'matched: ' + matched if matched else 'NOT matched (no existing topic fits).'}\n\n"
        f'User question: "{state["query"]}"\n'
        f'Answer given: "{state["answer"]}"'
    )

    decider = llm.with_structured_output(Decision)
    decision: Decision = decider.invoke(prompt)

    action = decision.action
    if action == "append" and not matched:
        # can't append without a match — fall back to create
        action = "create"

    trace = [f"decision_worth: action={action}"]
    if decision.low_confidence:
        trace.append("decision_worth: low-confidence classification")

    result: dict = {"memory_action": action, "trace": trace}

    if action in ("append", "create"):
        result["memory_category"] = decision.category or "general"
        result["topic_title"] = decision.title or state["query"][:60]
        result["topic_one_liner"] = decision.one_liner or ""
        result["topic_summary"] = decision.summary or ""
        result["topic_keywords"] = decision.keywords or []
        if decision.keywords:
            trace.append(f"decision_worth: keywords={', '.join(decision.keywords)}")
    elif action == "profile":
        result["profile_update"] = decision.profile_update or ""

    return result
