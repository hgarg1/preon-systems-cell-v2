"""LLM provider adapters for the Ribosome.

Each adapter is a thin wrapper around a provider SDK. Import errors are caught
at construction time so missing optional dependencies degrade gracefully to stub.

API keys are read from environment variables:
  ANTHROPIC_API_KEY, OPENAI_API_KEY, XAI_API_KEY, GEMINI_API_KEY

Grok uses the official xai-sdk (gRPC-based), not the OpenAI-compatible REST layer.
Install: pip install preon-systems-cell[grok]
"""
from __future__ import annotations

import os
from typing import Protocol, runtime_checkable

# Default model IDs per provider × model class.
# Overridden by GenomeModule.llm_model_id when set.
_MODEL_MAP: dict[str, dict[str, str]] = {
    "anthropic": {
        "fast": "claude-haiku-4-5-20251001",
        "standard": "claude-sonnet-4-6",
        "reasoning": "claude-opus-4-8",
    },
    "openai": {
        "fast": "gpt-4o-mini",
        "standard": "gpt-4o",
        "reasoning": "o3",
    },
    "grok": {
        "fast": "grok-3-mini-fast",
        "standard": "grok-3",
        "reasoning": "grok-3-mini",
    },
    "gemini": {
        "fast": "gemini-2.0-flash",
        "standard": "gemini-2.5-pro",
        "reasoning": "gemini-2.5-pro",
    },
}

_ENV_KEYS: dict[str, str] = {
    "anthropic": "ANTHROPIC_API_KEY",
    "openai": "OPENAI_API_KEY",
    "grok": "XAI_API_KEY",
    "gemini": "GEMINI_API_KEY",
}


@runtime_checkable
class LlmAdapter(Protocol):
    def complete(self, prompt: str, system: str | None = None, max_tokens: int = 2048) -> str: ...


class _AnthropicAdapter:
    def __init__(self, model_id: str) -> None:
        import anthropic  # pip install anthropic
        self._client = anthropic.Anthropic()
        self._model = model_id

    def complete(self, prompt: str, system: str | None = None, max_tokens: int = 2048) -> str:
        msg = self._client.messages.create(
            model=self._model,
            max_tokens=max_tokens,
            system=system or "You are a helpful assistant.",
            messages=[{"role": "user", "content": prompt}],
        )
        return msg.content[0].text  # type: ignore[union-attr]


class _OpenAIAdapter:
    """Handles both OpenAI and xAI Grok (same API shape, different base_url)."""

    def __init__(self, model_id: str, base_url: str | None = None, api_key_env: str = "OPENAI_API_KEY") -> None:
        import openai  # pip install openai
        kwargs: dict = {"api_key": os.environ[api_key_env]}
        if base_url:
            kwargs["base_url"] = base_url
        self._client = openai.OpenAI(**kwargs)
        self._model = model_id

    def complete(self, prompt: str, system: str | None = None, max_tokens: int = 2048) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        resp = self._client.chat.completions.create(
            model=self._model,
            messages=messages,  # type: ignore[arg-type]
            max_tokens=max_tokens,
        )
        return resp.choices[0].message.content or ""


class _GrokNativeAdapter:
    """Official xAI SDK adapter — gRPC-based, not the OpenAI-compatibility layer.

    pip install xai-sdk
    Docs: https://docs.x.ai
    """

    def __init__(self, model_id: str) -> None:
        from xai_sdk import Client  # pip install xai-sdk
        from xai_sdk.chat import user as _user
        self._client = Client()  # reads XAI_API_KEY from env
        self._user_msg = _user
        self._model = model_id

    def complete(self, prompt: str, system: str | None = None, max_tokens: int = 2048) -> str:
        chat = self._client.chat.create(model=self._model)
        full_prompt = f"{system}\n\n{prompt}" if system else prompt
        chat.append(self._user_msg(full_prompt))
        response = chat.sample()
        return response.content


class _GeminiAdapter:
    def __init__(self, model_id: str) -> None:
        import google.generativeai as genai  # pip install google-generativeai
        genai.configure(api_key=os.environ["GEMINI_API_KEY"])
        self._model = genai.GenerativeModel(model_id)
        self._model_id = model_id

    def complete(self, prompt: str, system: str | None = None, max_tokens: int = 2048) -> str:
        full_prompt = f"{system}\n\n{prompt}" if system else prompt
        resp = self._model.generate_content(
            full_prompt,
            generation_config={"max_output_tokens": max_tokens},
        )
        return resp.text


def get_adapter(provider: str, model_class: str, model_id: str | None = None) -> LlmAdapter | None:
    """Return a live adapter if the provider API key is set, else None.

    Returns None (caller should fall back to stub) when:
    - The env var is missing
    - The provider SDK is not installed
    - The provider/model_class is unknown
    """
    env_key = _ENV_KEYS.get(provider)
    if not env_key or not os.environ.get(env_key):
        return None

    resolved_model = model_id or _MODEL_MAP.get(provider, {}).get(model_class)
    if not resolved_model:
        return None

    try:
        if provider == "anthropic":
            return _AnthropicAdapter(resolved_model)
        if provider == "openai":
            return _OpenAIAdapter(resolved_model)
        if provider == "grok":
            return _GrokNativeAdapter(resolved_model)
        if provider == "gemini":
            return _GeminiAdapter(resolved_model)
    except ImportError:
        pass  # SDK not installed — caller falls back to stub
    return None
