import json
import re
from dataclasses import dataclass
from typing import Optional
from anthropic import Anthropic
from core.config import settings


@dataclass
class LLMResponse:
    content: str
    usage: dict
    model: str


class LLMClient:
    def __init__(self):
        self.provider = settings.LLM_PROVIDER
        if self.provider == "claude" and settings.ANTHROPIC_API_KEY:
            self._client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
            self._model = settings.ANTHROPIC_MODEL
        else:
            self._client = None
            self._model = None

    async def chat(self, system: str, user: str, temperature: float = 0.3, max_tokens: int = 2048) -> LLMResponse:
        if self.provider == "claude" and self._client:
            return await self._claude_chat(system, user, temperature, max_tokens)
        else:
            return await self._openai_chat(system, user, temperature, max_tokens)

    async def _claude_chat(self, system: str, user: str, temperature: float, max_tokens: int) -> LLMResponse:
        resp = self._client.messages.create(
            model=self._model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return LLMResponse(
            content=resp.content[0].text,
            usage={"input": resp.usage.input_tokens, "output": resp.usage.output_tokens},
            model=resp.model,
        )

    async def _openai_chat(self, system: str, user: str, temperature: float, max_tokens: int) -> LLMResponse:
        import httpx
        headers = {
            "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": settings.OPENAI_MODEL,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
            data = resp.json()
        return LLMResponse(
            content=data["choices"][0]["message"]["content"],
            usage=data.get("usage", {}),
            model=data["model"],
        )

    async def chat_with_json_output(self, system: str, user: str, temperature: float = 0.2) -> dict:
        """Call LLM and parse JSON from response."""
        resp = await self.chat(system, user, temperature, max_tokens=4096)
        json_str = resp.content
        match = re.search(r"\{.*\}", json_str, re.DOTALL)
        if match:
            json_str = match.group(0)
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            return {"raw": resp.content, "error": "Failed to parse JSON"}


llm_client = LLMClient()
