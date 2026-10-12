from .models import Memory
from .providers import AnthropicProvider, OpenAICompatibleProvider, Provider
from .storage import MemoryStore


class MemoryAgent:
    def __init__(self, provider: Provider, store: MemoryStore | None = None) -> None:
        self.provider = provider
        self.store = store or MemoryStore()

    def remember(self, content: str, kind: str = "fact", importance: int = 3,
                 source: str = "user") -> Memory:
        memory = Memory(content=content, kind=kind, importance=importance, source=source)
        return self.store.save(memory)

    def recall(self, query: str, limit: int = 8) -> list[Memory]:
        return self.store.search(query, limit)

    def chat(self, message: str) -> str:
        memories = self.recall(message)
        context = "\n".join(f"- [{m.kind}] {m.content}" for m in memories) or "(no relevant memory)"
        messages = [
            {"role": "system", "content": (
                "You are a helpful assistant with persistent memory. Use the memory "
                "only when relevant; do not invent facts.\n\nRelevant memory:\n" + context
            )},
            {"role": "user", "content": message},
        ]
        answer = self.provider.complete(messages)
        return answer


def provider_from_env():
    import os
    kind = os.getenv("MEMORY_AGENT_PROVIDER", "openai-compatible").lower()
    api_key = os.getenv("MEMORY_AGENT_API_KEY", "")
    model = os.getenv("MEMORY_AGENT_MODEL", "gpt-4o-mini")
    base_url = os.getenv("MEMORY_AGENT_BASE_URL", "https://api.openai.com/v1")
    if kind == "anthropic":
        return AnthropicProvider(api_key, model, base_url)
    return OpenAICompatibleProvider(api_key, model, base_url)
