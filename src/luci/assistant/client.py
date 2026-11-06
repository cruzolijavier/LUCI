"""Calls to OpenAI: chat (Responses API with tools), transcription and embeddings.

Everything here runs outside the GUI thread (see session.py); there is no Qt here.
"""

from __future__ import annotations

from . import config as cfg

try:
    from openai import APIConnectionError, APIStatusError, AuthenticationError, OpenAI, RateLimitError
except Exception:  # without the library the assistant explains instead of breaking LUCI
    OpenAI = None
    AuthenticationError = RateLimitError = APIConnectionError = APIStatusError = Exception


class AssistantError(Exception):
    """An error already worded for the user."""


_clients: dict = {}


def client():
    if OpenAI is None:
        raise AssistantError("The 'openai' Python package is missing. Install it with: "
                             "python -m pip install openai")
    key, error = cfg.read_key()
    if error:
        raise AssistantError(error)
    if key not in _clients:
        _clients.clear()
        _clients[key] = OpenAI(api_key=key, timeout=120, max_retries=2)
    return _clients[key]


def explain_error(error: Exception) -> str:
    if isinstance(error, AssistantError):
        return str(error)
    if isinstance(error, AuthenticationError):
        return "OpenAI rejected the key. Check it in Tools > Settings > OpenAI API key (or openai_key.txt)."
    if isinstance(error, RateLimitError):
        text = str(error).lower()
        if "quota" in text or "billing" in text or "insufficient" in text:
            return "The OpenAI account has no credit left. Top it up at platform.openai.com (Billing)."
        return "OpenAI's per-minute limit was reached. Wait a few seconds and ask again."
    if isinstance(error, APIConnectionError):
        return "No connection to OpenAI. Check the internet connection (or the proxy/firewall)."
    if isinstance(error, APIStatusError):
        return f"OpenAI returned an error ({getattr(error, 'status_code', '?')}): {getattr(error, 'message', error)}"
    return f"Unexpected assistant error: {error}"


def respond(instructions: str, items: list, tools: list, previous_id: str | None = None):
    """One call to the model. ``items`` are messages, or the outputs of tool calls."""
    params = dict(model=cfg.MODEL, instructions=instructions, input=items,
                  reasoning={"effort": cfg.REASONING_EFFORT}, max_output_tokens=cfg.MAX_OUTPUT_TOKENS,
                  text={"verbosity": "low"})
    if tools:
        params["tools"] = tools
        params["parallel_tool_calls"] = True
    if previous_id:
        params["previous_response_id"] = previous_id
    return client().responses.create(**params)


def transcribe(audio_path: str, hint: str = "") -> str:
    """Audio (wav) -> text. ``hint`` helps with program names and jargon."""
    api = client()
    last = None
    for model in (cfg.MODEL_TRANSCRIPTION, cfg.MODEL_TRANSCRIPTION_FALLBACK):
        try:
            with open(audio_path, "rb") as handle:
                result = api.audio.transcriptions.create(model=model, file=handle, prompt=hint[:600])
            text = (result.text or "").strip()
            return "" if _echo(text, hint) else text
        except (AuthenticationError, APIConnectionError, RateLimitError):
            raise
        except Exception as exc:
            last = exc
    raise last


def _echo(text: str, hint: str) -> bool:
    """With near-empty audio some models return the hint itself: that is not what was said."""
    words = [w for w in text.lower().replace(",", " ").split() if len(w) > 2]
    if len(words) < 6:
        return False
    vocabulary = set(hint.lower().replace(",", " ").split())
    return sum(w in vocabulary for w in words) / len(words) > 0.7


def embeddings(texts: list[str]) -> list[list[float]]:
    result = client().embeddings.create(model=cfg.MODEL_EMBEDDINGS, input=texts)
    return [item.embedding for item in result.data]
