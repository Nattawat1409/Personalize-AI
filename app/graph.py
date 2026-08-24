from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph

from app.models.states.state import State
from app.nodes.append_md import append_md
from app.nodes.assemble_content import assemble_content
from app.nodes.create_md import create_md
from app.nodes.decision_worth import decision_worth
from app.nodes.generate_answer import generate_answer
from app.nodes.loading_userProfiles import loading_userProfiles
from app.nodes.search_TopicIndex import search_TopicIndex
from app.nodes.specific_topic import specific_topic
from app.nodes.update_UserProfile import update_UserProfile


def route_after_search(state: State) -> str:
    return "specific_topic" if state.get("matched_topic_id") else "assemble_content"


def route_after_decision(state: State) -> str:
    action = state.get("memory_action", "skip")
    return {
        "skip": END,
        "append": "append_md",
        "create": "create_md",
        "profile": "update_UserProfile",
    }[action]


def build_graph():
    graph = StateGraph(State)

    graph.add_node("loading_userProfiles", loading_userProfiles)
    graph.add_node("search_TopicIndex", search_TopicIndex)
    graph.add_node("specific_topic", specific_topic)
    # defer=True: assemble_content has two incoming paths of different depth
    # (loading_userProfiles is 1 hop from START; the topic-search path is 1
    # hop on no-match but 2 hops via specific_topic on a match). Without
    # defer, LangGraph's default OR-join runs this node once per predecessor
    # instead of once after both — verified empirically.
    graph.add_node("assemble_content", assemble_content, defer=True)
    graph.add_node("generate_answer", generate_answer)
    graph.add_node("decision_worth", decision_worth)
    graph.add_node("append_md", append_md)
    graph.add_node("create_md", create_md)
    graph.add_node("update_UserProfile", update_UserProfile)

    graph.add_edge(START, "loading_userProfiles")
    graph.add_edge(START, "search_TopicIndex")

    graph.add_edge("loading_userProfiles", "assemble_content")
    graph.add_conditional_edges(
        "search_TopicIndex",
        route_after_search,
        {"specific_topic": "specific_topic", "assemble_content": "assemble_content"},
    )
    graph.add_edge("specific_topic", "assemble_content")

    graph.add_edge("assemble_content", "generate_answer")
    graph.add_edge("generate_answer", "decision_worth")

    graph.add_conditional_edges(
        "decision_worth",
        route_after_decision,
        {
            END: END,
            "append_md": "append_md",
            "create_md": "create_md",
            "update_UserProfile": "update_UserProfile",
        },
    )
    graph.add_edge("append_md", END)
    graph.add_edge("create_md", END)
    graph.add_edge("update_UserProfile", END)

    return graph.compile(checkpointer=InMemorySaver())
