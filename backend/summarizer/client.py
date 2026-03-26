from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod

import anthropic

logger = logging.getLogger(__name__)


class LLMClient(ABC):
    @abstractmethod
    async def complete(self, messages: list[dict], tools: list[dict]) -> str:
        """Call the LLM and return the tool-use JSON string."""


class AnthropicLLMClient(LLMClient):
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-6") -> None:
        self._client = anthropic.AsyncAnthropic(api_key=api_key)
        self._model = model

    async def complete(self, messages: list[dict], tools: list[dict]) -> str:
        response = await self._client.messages.create(
            model=self._model,
            max_tokens=4096,
            tools=tools,
            messages=messages,
        )
        for block in response.content:
            if block.type == "tool_use":
                return json.dumps(block.input)
        raise ValueError("LLM did not return a tool_use block")


class StubLLMClient(LLMClient):
    def __init__(self, response: str) -> None:
        self._response = response

    async def complete(self, messages: list[dict], tools: list[dict]) -> str:
        return self._response
