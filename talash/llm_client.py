import os
import litellm
import json
import re
from typing import Type, TypeVar, Any, Union
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

os.environ.pop("OPENROUTER_API_BASE", None)

T = TypeVar("T", bound=BaseModel)


class LLMClient:
    def __init__(self):
        self.groq_keys    = [os.getenv(f"LITELLM_GROQ_API_KEY{i}")   for i in range(1, 6)]
        self.gemini_keys  = [os.getenv(f"LITELLM_GEMINI_API_KEY{i}") for i in range(1, 6)]

        self.groq_keys   = [k for k in self.groq_keys   if k]
        self.gemini_keys = [k for k in self.gemini_keys if k]

        self.groq_index   = 0
        self.gemini_index = 0
        self.openrouter_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENROUTER_KEY")

    def _get_next_groq_key(self):
        if not self.groq_keys:
            return os.getenv("GROQ_API_KEY") or ""
        key = self.groq_keys[self.groq_index % len(self.groq_keys)]
        self.groq_index += 1
        return key

    def _get_next_gemini_key(self):
        if not self.gemini_keys:
            return os.getenv("GEMINI_API_KEY") or ""
        key = self.gemini_keys[self.gemini_index % len(self.gemini_keys)]
        self.gemini_index += 1
        return key

    # ------------------------------------------------------------------
    # Shared response wrapper
    # ------------------------------------------------------------------
    class _LLMResponse:
        def __init__(self, content: str):
            self.content = content
        def __str__(self):
            return self.content

    # ------------------------------------------------------------------
    # litellm_chat — three-tier fallback: Groq → Gemini → OpenRouter/auto
    # ------------------------------------------------------------------
    def litellm_chat(
        self,
        user_prompt: Union[str, list],
        system_prompt: str = None,
        provider: str = "groq",
    ):
        """
        Chat completion with automatic provider rotation and fallback.

        Fallback chain:
          1. Groq  (llama-3.3-70b-versatile) — fast, free tier
          2. Gemini (gemini-2.0-flash)        — FIX: was gemini-1.5-flash (404)
          3. OpenRouter /auto                 — free, picks best available model
        """
        messages = self._build_messages(user_prompt, system_prompt)

        # ── Provider selection ─────────────────────────────────────────
        if provider == "groq":
            model   = "groq/llama-3.3-70b-versatile"
            api_key = self._get_next_groq_key()
        elif provider == "gemini":
            # FIX: gemini-1.5-flash was removed from Google API (returns 404).
            # gemini-2.0-flash is the current stable replacement.
            model   = "gemini/gemini-2.0-flash"
            api_key = self._get_next_gemini_key()
        else:  # provider == "openrouter"
            model   = "openrouter/auto"
            api_key = self.openrouter_key

        try:
            kwargs = dict(model=model, messages=messages, temperature=0.7)
            if api_key:
                kwargs["api_key"] = api_key
            if provider == "openrouter":
                kwargs["base_url"] = "https://openrouter.ai/api/v1"

            response = litellm.completion(**kwargs)
            return self._LLMResponse(response.choices[0].message.content)

        except Exception as e:
            # ── Fallback cascade ──────────────────────────────────────
            if provider == "groq":
                print(f" Groq failed, falling back to Gemini: {e}")
                return self.litellm_chat(user_prompt, system_prompt, provider="gemini")

            if provider == "gemini":
                if self.openrouter_key:
                    print(f" Gemini failed, falling back to OpenRouter/auto: {e}")
                    return self.litellm_chat(user_prompt, system_prompt, provider="openrouter")
                print(f" LiteLLM chat failed (no OpenRouter key): {e}")
                raise e

            # openrouter was last resort
            print(f" LiteLLM chat failed (all providers exhausted): {e}")
            raise e

    # ------------------------------------------------------------------
    # openrouter_structured_call — structured JSON extraction via GPT-4o
    # ------------------------------------------------------------------
    def openrouter_structured_call(self, prompt: str, response_model: Type[T]) -> T:
        """
        OpenRouter GPT-4o call for structured extraction.
        Falls back to openrouter/auto if gpt-4o fails.
        """
        if not self.openrouter_key:
            raise ValueError("OPENROUTER_API_KEY or OPENROUTER_KEY not found in environment")

        for model in ["openrouter/openai/gpt-4o", "openrouter/auto"]:
            try:
                response = litellm.completion(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    api_key=self.openrouter_key,
                    base_url="https://openrouter.ai/api/v1",
                    max_tokens=1000,
                )
                content  = response.choices[0].message.content
                json_str = re.sub(
                    r"^```json\s*|^```\s*|```$", "",
                    content, flags=re.MULTILINE
                ).strip()
                return response_model.model_validate_json(json_str)

            except Exception as e:
                print(f" {model} structured call failed: {e}")
                if model == "openrouter/auto":
                    raise e

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _build_messages(
        self,
        user_prompt: Union[str, list],
        system_prompt: str = None,
    ) -> list:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        if isinstance(user_prompt, str):
            messages.append({"role": "user", "content": user_prompt})
        elif isinstance(user_prompt, list):
            for msg in user_prompt:
                if hasattr(msg, "content"):
                    msg_type = msg.__class__.__name__
                    if "System" in msg_type:
                        role = "system"
                    elif "AI" in msg_type:
                        role = "assistant"
                    else:
                        role = "user"
                    messages.append({"role": role, "content": msg.content})
                elif isinstance(msg, dict) and "role" in msg:
                    messages.append(msg)
                else:
                    messages.append({"role": "user", "content": str(msg)})
        return messages


# Global singleton
_client = LLMClient()


def litellm_chat(user_prompt, system_prompt=None, provider="groq"):
    return _client.litellm_chat(user_prompt, system_prompt, provider)


def openrouter_structured_call(prompt: str, response_model: Type[T]) -> T:
    return _client.openrouter_structured_call(prompt, response_model)
