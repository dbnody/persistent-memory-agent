import argparse
import os

from .agent import MemoryAgent, provider_from_env
from .storage import MemoryStore


def main() -> None:
    parser = argparse.ArgumentParser(description="Provider-agnostic persistent memory agent")
    parser.add_argument("command", choices=["chat", "remember", "recall", "export"])
    parser.add_argument("text", nargs="*")
    parser.add_argument("--db", default=os.getenv("MEMORY_AGENT_DB", "data/memory.db"))
    args = parser.parse_args()
    store = MemoryStore(args.db)
    agent = MemoryAgent(provider_from_env(), store)
    text = " ".join(args.text).strip()
    if args.command == "remember":
        print(agent.remember(text).id)
    elif args.command == "recall":
        for memory in agent.recall(text):
            print(f"[{memory.kind}] {memory.content}")
    elif args.command == "export":
        target = text or "data/memory-export.json"
        store.export_json(target)
        print(target)
    else:
        print(agent.chat(text))


if __name__ == "__main__":
    main()
