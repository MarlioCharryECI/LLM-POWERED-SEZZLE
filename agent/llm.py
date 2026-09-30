"""Provider-agnostic LLM layer. Default backend: Ollama (local, $0).

One entry point — `chat_json(system, user, schema)` — that returns a parsed dict
matching `schema`. Callers never see provider details. Selection is by env:

    SEZZLE_PROVIDER = ollama (default) | anthropic | openai
    SEZZLE_MODEL    = qwen2.5:7b-instruct (default)
    SEZZLE_OLLAMA_URL = http://localhost:11434

Design decisions that back the ADRs:
- SCHEMA-CONSTRAINED OUTPUT: we pass a JSON schema to the backend so decoding is
  grammar-constrained to valid JSON of the right shape. This is what makes a 7B
  model reliable enough to build on, and it *structurally* suppresses any
  reasoning/<think> preamble — there is no room in the grammar for it. (ADR:
  structured output / guardrails.)
- TEMPERATURE 0: deterministic outputs so the first-vs-final eval delta reflects
  our changes, not sampling noise. Evidence-generating over clever.
- STDLIB-ONLY OLLAMA CALL: no SDK dependency for the default path; anthropic /
  openai are imported lazily only if selected, so $0 local needs nothing installed.
"""

import json
import os
import urllib.error
import urllib.request

PROVIDER = os.environ.get("SEZZLE_PROVIDER", "ollama").lower()
DEFAULT_MODEL = os.environ.get("SEZZLE_MODEL", "qwen2.5:7b")
OLLAMA_URL = os.environ.get("SEZZLE_OLLAMA_URL", "http://localhost:11434")


def _loads_lenient(text: str) -> dict:
    """Parse JSON, tolerating stray prose/code fences around the object."""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start != -1 and end > start:
            return json.loads(text[start : end + 1])
        raise


# --------------------------------------------------------------------------- #
# Ollama (default)                                                            #
# --------------------------------------------------------------------------- #
def _ollama_chat_json(system, user, schema, model):
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "stream": False,
        "format": schema,                 # grammar-constrained to this schema
        "options": {"temperature": 0},    # deterministic
    }
    req = urllib.request.Request(
        f"{OLLAMA_URL}/api/chat",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    # Generous timeout: the first call cold-loads the model into VRAM.
    with urllib.request.urlopen(req, timeout=180) as resp:
        body = json.loads(resp.read().decode("utf-8"))
    return _loads_lenient(body["message"]["content"])


# --------------------------------------------------------------------------- #
# Optional paid backends — same interface, imported only if selected.         #
# --------------------------------------------------------------------------- #
def _anthropic_chat_json(system, user, schema, model):
    import anthropic  # lazy

    client = anthropic.Anthropic()
    # Nudge JSON-only; Anthropic has no schema-grammar, so we lean on the parser.
    sys_json = system + "\n\nRespond with ONLY a JSON object, no other text."
    msg = client.messages.create(
        model=model if model != DEFAULT_MODEL else "claude-haiku-4-5-20251001",
        max_tokens=1024,
        system=[{"type": "text", "text": sys_json,
                 "cache_control": {"type": "ephemeral"}}],
        messages=[{"role": "user", "content": user}],
    )
    text = "".join(b.text for b in msg.content if b.type == "text")
    return _loads_lenient(text)


def _openai_chat_json(system, user, schema, model):
    import openai  # lazy

    client = openai.OpenAI()
    resp = client.chat.completions.create(
        model=model if model != DEFAULT_MODEL else "gpt-4o-mini",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {"name": "reply", "schema": schema, "strict": False},
        },
        temperature=0,
    )
    return _loads_lenient(resp.choices[0].message.content)


_BACKENDS = {
    "ollama": _ollama_chat_json,
    "anthropic": _anthropic_chat_json,
    "openai": _openai_chat_json,
}


def chat_json(system: str, user: str, schema: dict, model: str = None) -> dict:
    """Send one turn, return a parsed dict conforming to `schema`.

    Raises on transport/parse failure; the agent turns that into a safe escalate.
    """
    backend = _BACKENDS.get(PROVIDER)
    if backend is None:
        raise ValueError(f"unknown SEZZLE_PROVIDER: {PROVIDER}")
    return backend(system, user, schema, model or DEFAULT_MODEL)
