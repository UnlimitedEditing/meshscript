"""
OpenRouter VLM/LLM client — stdlib only (urllib), no third-party HTTP deps.

Free models as of June 2026 — run list_free_models() to refresh.

Vision-capable (text+image->text):
  google/gemma-4-31b-it:free              -- best free vision model
  google/gemma-4-26b-a4b-it:free          -- MoE variant (faster)
  moonshotai/kimi-k2.6:free
  nvidia/nemotron-nano-12b-v2-vl:free

Text/code:
  qwen/qwen3-coder:free                   -- code specialist, 1M ctx (strips <think> blocks)
  meta-llama/llama-3.3-70b-instruct:free
  nvidia/nemotron-3-ultra-550b-a55b:free
  openai/gpt-oss-120b:free
"""

import base64
import json
import os
import ssl
import urllib.request
import urllib.error

OPENROUTER_BASE = "https://openrouter.ai/api/v1/chat/completions"

DEFAULT_VLM_MODEL      = "google/gemma-4-31b-it:free"
DEFAULT_DESIGNER_MODEL = "qwen/qwen3-coder:free"


def _ssl_context():
    """
    Return an SSL context that works on Python 3.14 Windows where the default
    context can reject certs that violate the 'Basic Constraints must be critical'
    rule (RFC 5280 strict enforcement added in 3.14).
    Try certifi first; fall back to no-verify.
    """
    try:
        import certifi
        ctx = ssl.create_default_context(cafile=certifi.where())
        return ctx
    except ImportError:
        pass
    try:
        ctx = ssl.create_default_context()
        return ctx
    except Exception:
        pass
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.check_hostname = False
    ctx.verify_mode    = ssl.CERT_NONE
    return ctx


_CTX = _ssl_context()


class VLMClient:
    def __init__(self, api_key: str = None, model: str = DEFAULT_VLM_MODEL):
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY", "")
        if not self.api_key:
            raise ValueError(
                "OpenRouter API key required.\n"
                "  Set env var: OPENROUTER_API_KEY=sk-or-...\n"
                "  Or pass:     VLMClient(api_key='sk-or-...')\n"
                "  Get a key:   https://openrouter.ai/keys"
            )
        self.model = model

    def chat(self, messages: list, temperature: float = 0.2, _retries: int = 4) -> str:
        """Send messages to the model, return the text response. Auto-retries on 429."""
        import time

        payload = json.dumps({
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }).encode()

        for attempt in range(_retries + 1):
            req = urllib.request.Request(
                OPENROUTER_BASE,
                data=payload,
                headers={
                    "Authorization":  f"Bearer {self.api_key}",
                    "Content-Type":   "application/json",
                    "HTTP-Referer":   "https://github.com/UnlimitedEditing/meshscript",
                    "X-Title":        "MeshScript",
                },
                method="POST",
            )
            try:
                with urllib.request.urlopen(req, timeout=90, context=_CTX) as resp:
                    body = json.loads(resp.read())
                    break  # success
            except urllib.error.HTTPError as e:
                raw = e.read().decode()
                if e.code == 429 and attempt < _retries:
                    wait = _parse_retry_after(raw)
                    print(f" [rate-limited — waiting {wait}s]", flush=True)
                    time.sleep(wait)
                    continue
                if e.code == 404 and "unavailable for free" in raw:
                    raise RuntimeError(
                        f"Model '{self.model}' is no longer free on OpenRouter.\n"
                        f"  Run: python -c \"from critique.client import list_free_models; list_free_models()\"\n"
                        f"  Then set OPENROUTER_DESIGNER_MODEL / OPENROUTER_VLM_MODEL in .env\n"
                        f"  Raw: {raw}"
                    ) from e
                raise RuntimeError(f"OpenRouter HTTP {e.code}: {raw}") from e

        # Surface model-level errors (context-length exceeded, moderation, etc.)
        if "error" in body:
            raise RuntimeError(f"OpenRouter error: {body['error']}")

        return body["choices"][0]["message"]["content"]


def _parse_retry_after(raw: str, default: float = 10.0) -> float:
    """Extract retry_after_seconds from a 429 response body, with a fallback."""
    try:
        data = json.loads(raw)
        secs = data["error"]["metadata"].get("retry_after_seconds")
        if secs is not None:
            return float(secs) + 1.0  # add 1s buffer
    except Exception:
        pass
    return default


def list_free_models(api_key: str = None) -> list:
    """Fetch and print all free models from OpenRouter. Useful when defaults stop working."""
    key = api_key or os.environ.get("OPENROUTER_API_KEY", "")
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/models",
        headers={"Authorization": f"Bearer {key}"},
    )
    with urllib.request.urlopen(req, timeout=30, context=_CTX) as r:
        data = json.loads(r.read())
    free = [m for m in data["data"] if str(m.get("pricing", {}).get("prompt", "1")) == "0"]
    free.sort(key=lambda m: m["id"])
    for m in free:
        mods = m.get("architecture", {}).get("modality", "")
        ctx  = m.get("context_length", "?")
        print(f"  {m['id']:<65} ctx={ctx:<8} {mods}")
    return free


def image_content(image_bytes: bytes, mime: str = "image/png") -> dict:
    """Build an OpenAI-format image_url content part from raw PNG bytes."""
    b64 = base64.b64encode(image_bytes).decode()
    return {
        "type":      "image_url",
        "image_url": {"url": f"data:{mime};base64,{b64}"},
    }
