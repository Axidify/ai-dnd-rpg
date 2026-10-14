"""
LLM client abstraction for Gemini and vLLM (OpenAI-compatible) providers.
"""

import os
from types import SimpleNamespace
from typing import Any, Iterator, List, Optional

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

_GEMINI_MODULE = None
_GEMINI_CHECKED = False


def _get_genai():
    """Load google.generativeai only when Gemini provider is actually used."""
    global _GEMINI_MODULE, _GEMINI_CHECKED
    if _GEMINI_CHECKED:
        return _GEMINI_MODULE
    _GEMINI_CHECKED = True
    try:
        import google.generativeai as genai
        _GEMINI_MODULE = genai
    except ImportError:
        _GEMINI_MODULE = None
    return _GEMINI_MODULE


DM_GENERATION_CONFIG = {
    "temperature": 0.9,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 2048,
}


def get_llm_provider() -> str:
    """Return 'vllm' or 'gemini' based on environment configuration."""
    provider = os.getenv("LLM_PROVIDER", "").strip().lower()
    if provider in ("vllm", "openai"):
        return "vllm"
    if provider == "gemini":
        return "gemini"
    if os.getenv("VLLM_BASE_URL"):
        return "vllm"
    return "gemini"


def is_llm_configured() -> bool:
    if get_llm_provider() == "vllm":
        return bool(os.getenv("VLLM_BASE_URL") and os.getenv("VLLM_MODEL"))
    return bool(os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"))


def get_active_model_name() -> str:
    if get_llm_provider() == "vllm":
        return os.getenv("VLLM_MODEL", "unknown")
    return os.getenv("GEMINI_MODEL", "gemini-2.0-flash")


class VllmChat:
    """Stateful chat session compatible with the Gemini chat interface."""

    def __init__(self, client: "OpenAI", model: str, messages: List[dict]):
        self._client = client
        self._model = model
        self._messages = messages

    def send_message(self, content: str, stream: bool = False):
        self._messages.append({"role": "user", "content": content})
        if stream:
            return self._stream_response()
        return self._complete_response()

    def _complete_response(self):
        response = self._client.chat.completions.create(
            model=self._model,
            messages=self._messages,
            temperature=0.9,
            max_tokens=2048,
        )
        text = response.choices[0].message.content or ""
        self._messages.append({"role": "assistant", "content": text})
        return SimpleNamespace(text=text)

    def _stream_response(self) -> Iterator[SimpleNamespace]:
        stream = self._client.chat.completions.create(
            model=self._model,
            messages=self._messages,
            temperature=0.9,
            max_tokens=2048,
            stream=True,
        )

        chunks: List[str] = []

        def generator() -> Iterator[SimpleNamespace]:
            for chunk in stream:
                delta = chunk.choices[0].delta.content
                if delta:
                    chunks.append(delta)
                    yield SimpleNamespace(text=delta)
            self._messages.append({"role": "assistant", "content": "".join(chunks)})

        return generator()


class VllmModel:
    """Thin wrapper so vLLM can use the same start_chat() flow as Gemini."""

    def __init__(self, client: "OpenAI", model_name: str):
        self._client = client
        self._model_name = model_name

    def start_chat(self, history: List[dict]) -> VllmChat:
        messages = []
        for item in history:
            role = "user" if item["role"] == "user" else "assistant"
            messages.append({"role": role, "content": item["parts"][0]})
        return VllmChat(self._client, self._model_name, messages)


def create_dm_model() -> Optional[Any]:
    """Create the DM model for the configured provider."""
    provider = get_llm_provider()

    if provider == "vllm":
        if not OPENAI_AVAILABLE:
            print("   ❌ openai package not installed (required for vLLM)")
            return None

        base_url = os.getenv("VLLM_BASE_URL")
        model_name = os.getenv("VLLM_MODEL")
        if not base_url or not model_name:
            print("   ❌ VLLM_BASE_URL and VLLM_MODEL must be set for vLLM provider")
            return None

        api_key = os.getenv("VLLM_API_KEY", "EMPTY")
        client = OpenAI(base_url=base_url, api_key=api_key)
        print(f"   ✅ Using vLLM model: {model_name} at {base_url}")
        return VllmModel(client, model_name)

    genai = _get_genai()
    if not genai:
        print("   ❌ google-generativeai package not installed")
        return None

    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return None

    genai.configure(api_key=api_key)
    model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    model = genai.GenerativeModel(
        model_name=model_name,
        generation_config=DM_GENERATION_CONFIG,
    )
    print(f"   ✅ Using Gemini model: {model_name}")
    return model


def generate_text(
    prompt: str,
    *,
    temperature: float = 0.9,
    max_tokens: int = 2048,
    json_mode: bool = False,
    model_name: Optional[str] = None,
    max_retries: int = 1,
) -> Optional[str]:
    """One-shot text generation for arbiter and other non-chat callers."""
    provider = get_llm_provider()

    for attempt in range(max_retries):
        try:
            if provider == "vllm":
                if not OPENAI_AVAILABLE:
                    return None
                base_url = os.getenv("VLLM_BASE_URL")
                model = model_name or os.getenv("VLLM_MODEL")
                if not base_url or not model:
                    return None

                client = OpenAI(
                    base_url=base_url,
                    api_key=os.getenv("VLLM_API_KEY", "EMPTY"),
                )
                kwargs = {
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                }
                if json_mode:
                    kwargs["response_format"] = {"type": "json_object"}

                response = client.chat.completions.create(**kwargs)
                return response.choices[0].message.content

            genai = _get_genai()
            if not genai:
                return None

            api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
            if not api_key:
                return None

            genai.configure(api_key=api_key)
            model = model_name or os.getenv(
                "GEMINI_ARBITER_MODEL",
                os.getenv("GEMINI_MODEL", "gemini-2.0-flash"),
            )
            generation_config = {
                "temperature": temperature,
                "max_output_tokens": max_tokens,
            }
            if json_mode:
                generation_config["response_mime_type"] = "application/json"

            gemini_model = genai.GenerativeModel(
                model_name=model,
                generation_config=generation_config,
            )
            response = gemini_model.generate_content(prompt)
            return response.text
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"⚠️ LLM generate_text retry ({attempt + 1}/{max_retries}): {e}")
                continue
            print(f"❌ LLM generate_text failed: {e}")
            return None

    return None
