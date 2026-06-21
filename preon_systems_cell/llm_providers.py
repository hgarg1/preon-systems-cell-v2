"""LLM provider adapters for the Ribosome.

Each adapter is a thin wrapper around a provider SDK. Import errors are caught
at construction time so missing optional dependencies degrade gracefully to stub.

API keys are read from environment variables:
  ANTHROPIC_API_KEY, OPENAI_API_KEY, XAI_API_KEY, GEMINI_API_KEY

Grok intentionally uses the OpenAI-compatible REST endpoint (api.x.ai/v1) via the
openai SDK rather than the native xai-sdk. The xai-sdk uses gRPC with server-side
agentic tool calling (web search, X search, code execution) that runs autonomously
inside chat.sample() — violating the "one LLM call per protein" constraint. The
OpenAI-compatible path gives a plain, non-agentic single completion call.
"""
from __future__ import annotations

import os
import time
from typing import Callable, Protocol, runtime_checkable

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


def _retryable(exc: Exception) -> bool:
    """Return True if the exception represents a transient provider error worth retrying."""
    # Most provider SDKs surface HTTP status via .status_code or .response.status_code
    http_code = getattr(exc, "status_code", None) or getattr(
        getattr(exc, "response", None), "status_code", None
    )
    if isinstance(http_code, int) and http_code in (429, 500, 502, 503, 529):
        return True
    # google.api_core.exceptions use a numeric .code attribute (gRPC codes map to HTTP)
    grpc_code = getattr(exc, "code", None)
    if callable(grpc_code):
        grpc_code = grpc_code()
    if isinstance(grpc_code, int) and grpc_code in (8, 13, 14):  # ResourceExhausted, Internal, Unavailable
        return True
    return False


def _with_retry(fn: Callable[[], str], max_attempts: int = 2, base_delay: float = 1.0) -> str:
    """Run fn(), retrying once on transient provider errors with exponential back-off."""
    for attempt in range(max_attempts):
        try:
            return fn()
        except Exception as exc:
            if attempt < max_attempts - 1 and _retryable(exc):
                time.sleep(base_delay * (2 ** attempt))
                continue
            raise
    raise RuntimeError("unreachable")  # satisfies type checker


@runtime_checkable
class LlmAdapter(Protocol):
    def complete(
        self, prompt: str, system: str | None = None, max_tokens: int = 2048, timeout_seconds: int = 30
    ) -> str: ...


class _AnthropicAdapter:
    def __init__(self, model_id: str) -> None:
        import anthropic  # pip install anthropic
        self._client = anthropic.Anthropic()
        self._model = model_id

    def complete(
        self, prompt: str, system: str | None = None, max_tokens: int = 2048, timeout_seconds: int = 30
    ) -> str:
        return _with_retry(lambda: self._create(prompt, system, max_tokens, timeout_seconds))

    def _create(self, prompt: str, system: str | None, max_tokens: int, timeout_seconds: int) -> str:
        msg = self._client.messages.create(
            model=self._model,
            max_tokens=max_tokens,
            system=system or "You are a helpful assistant.",
            messages=[{"role": "user", "content": prompt}],
            timeout=timeout_seconds,
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

    def complete(
        self, prompt: str, system: str | None = None, max_tokens: int = 2048, timeout_seconds: int = 30
    ) -> str:
        return _with_retry(lambda: self._create(prompt, system, max_tokens, timeout_seconds))

    def _create(self, prompt: str, system: str | None, max_tokens: int, timeout_seconds: int) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        resp = self._client.chat.completions.create(
            model=self._model,
            messages=messages,  # type: ignore[arg-type]
            max_tokens=max_tokens,
            timeout=timeout_seconds,
        )
        return resp.choices[0].message.content or ""


class _GeminiAdapter:
    def __init__(self, model_id: str) -> None:
        import google.generativeai as genai  # pip install google-generativeai
        genai.configure(api_key=os.environ["GEMINI_API_KEY"])
        self._model = genai.GenerativeModel(model_id)
        self._model_id = model_id

    def complete(
        self, prompt: str, system: str | None = None, max_tokens: int = 2048, timeout_seconds: int = 30
    ) -> str:
        return _with_retry(lambda: self._create(prompt, system, max_tokens, timeout_seconds))

    def _create(self, prompt: str, system: str | None, max_tokens: int, timeout_seconds: int) -> str:
        full_prompt = f"{system}\n\n{prompt}" if system else prompt
        resp = self._model.generate_content(
            full_prompt,
            generation_config={"max_output_tokens": max_tokens},
            request_options={"timeout": timeout_seconds},
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
            return _OpenAIAdapter(
                resolved_model,
                base_url="https://api.x.ai/v1",
                api_key_env="XAI_API_KEY",
            )
        if provider == "gemini":
            return _GeminiAdapter(resolved_model)
    except ImportError:
        pass  # SDK not installed — caller falls back to stub
    return None
