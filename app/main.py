import uuid

from app.graph import build_graph


def main():
    graph = build_graph()
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    print("Personalize-AI POC — terminal chat. Type 'exit' or 'quit' to leave.\n")

    while True:
        try:
            query = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not query:
            continue
        if query.lower() in ("exit", "quit"):
            break

        prior_trace_len = len(graph.get_state(config).values.get("trace", []))
        result = graph.invoke({"query": query, "messages": [], "trace": []}, config=config)

        print(f"\nAgent: {result['answer']}\n")
        print("--- memory ---")
        for line in result.get("trace", [])[prior_trace_len:]:
            print(f"  {line}")
        print()


if __name__ == "__main__":
    main()
