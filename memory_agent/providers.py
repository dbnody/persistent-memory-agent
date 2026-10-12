import json
import urllib.request
from dataclasses import dataclass
from typing import Protocol


class Provider(Protocol):
    def complete(self, messages: list[dict[str, str]]) -> str: ...


@dataclass
class OpenAICompatibleProvider:
    """Works with OpenAI-compatible gateways and many local model servers."""

    api_key: str
    model: str
    base_url: str = "https://api.openai.com/v1"

    def complete(self, messages: list[dict[str, str]]) -> str:
        payload = json.dumps({"model": self.model, "messages": messages}).encode()
        request = urllib.request.Request(
            self.base_url.rstrip("/") + "/chat/completions",
            data=payload,
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {self.api_key}"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=120) as response:
            body = json.loads(response.read().decode("utf-8"))
        return body["choices"][0]["message"]["content"]


@dataclass
class AnthropicProvider:
    api_key: str
    model: str
    base_url: str = "https://api.anthropic.com/v1"

    def complete(self, messages: list[dict[str, str]]) -> str:
        system = "\n".join(m["content"] for m in messages if m["role"] == "system")
        user_messages = [m for m in messages if m["role"] != "system"]
        payload = {"model": self.model, "max_tokens": 2048, "messages": user_messages}
        if system:
            payload["system"] = system
        request = urllib.request.Request(
            self.base_url.rstrip("/") + "/messages",
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json", "x-api-key": self.api_key,
                     "anthropic-version": "2023-06-01"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=120) as response:
            body = json.loads(response.read().decode("utf-8"))
        return body["content"][0]["text"]
