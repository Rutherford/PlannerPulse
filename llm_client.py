"""
Elysia LLM Client (OpenAI-compatible shim)
==========================================

PlannerPulse historically called OpenAI directly. This module replaces that
with Informa's internal Elysia API while preserving the *exact* call shape the
existing modules use:

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": "..."},
                  {"role": "user", "content": "..."}],
        response_format={"type": "json_object"},
        temperature=0.4,
        max_tokens=4000,
    )
    text = response.choices[0].message.content

Internally the call is translated to Elysia's `/v2/ai/chat/completion`:

    POST {ELYSIA_API_BASE}/v2/ai/chat/completion
    Authorization: Bearer <JWT minted from the Cognito IDP>
    {
        "appId": "<your-app-id>",
        "query": "<flattened system + user prompt>",
        "name_of_model": "gpt-4o",
        "model": "azure",
        "tokens": 8192,
        "response_language": "English (US)",
        "chat_session": "<uuid>",
        "output_type": "markdown",
        "collection_name": "content_vectorstore"
    }

The reply (`{"question": ..., "answer": ..., "sources": [...]}`) is wrapped
back into the OpenAI response object shape so PlannerPulse callers don't have
to change.

Configuration (env vars)
------------------------
ELYSIA_API_BASE        Default: https://api.stage.ai.informa.com
ELYSIA_TOKEN_URL       Default: https://idp.dev.ai.informa.com/oauth2/token
ELYSIA_APP_ID          Required. Issued by the Elysia onboarding team.
ELYSIA_CLIENT_ID       Required. OAuth2 client_credentials client id.
ELYSIA_CLIENT_SECRET   Required. OAuth2 client_credentials client secret.
ELYSIA_SCOPE           Optional. OAuth2 scope (e.g. "elysia/api").
ELYSIA_DEFAULT_MODEL   Optional. Default name_of_model. Defaults to "gpt-4o".
ELYSIA_DEFAULT_PROVIDER Optional. "azure" or "aws". Defaults to "azure".
ELYSIA_COLLECTION      Optional. Default Elysia knowledge collection.
                       Defaults to "content_vectorstore".
"""

from __future__ import annotations

import base64
import json
import logging
import os
import re
import threading
import time
import urllib.parse
import urllib.request
import urllib.error
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Defaults / constants
# ---------------------------------------------------------------------------

DEFAULT_API_BASE = "https://api.stage.ai.informa.com"
DEFAULT_TOKEN_URL = "https://idp.dev.ai.informa.com/oauth2/token"
DEFAULT_MODEL = "gpt-4o"
DEFAULT_PROVIDER = "azure"  # 'azure' | 'aws'
DEFAULT_COLLECTION = "content_vectorstore"
DEFAULT_OUTPUT_TYPE = "markdown"  # 'markdown' | 'html'
DEFAULT_LANGUAGE = "English (US)"
COMPLETION_PATH = "/v2/ai/chat/completion"

# Map OpenAI model names PlannerPulse uses → Elysia's `name_of_model` enum.
# The Elysia spec advertises gpt-4o, gpt-5, gpt-5-mini, several Claude variants,
# and DeepSeek-V3. PlannerPulse uses gpt-4o (drafts, summaries) and gpt-4o-mini
# (cheap classifier). We map mini → gpt-5-mini as the closest cheap equivalent.
MODEL_MAP = {
    "gpt-4o": "gpt-4o",
    "gpt-4o-mini": "gpt-5-mini",
    "gpt-4": "gpt-4o",
    "gpt-4-turbo": "gpt-4o",
    "gpt-3.5-turbo": "gpt-5-mini",
}


def _resolve_model(name: str) -> str:
    """Translate an OpenAI model name to an Elysia `name_of_model` value.
    Unknown names pass through; if Elysia rejects them you'll see a 422."""
    return MODEL_MAP.get(name, name)


# ---------------------------------------------------------------------------
# OAuth2 token fetcher (Cognito client_credentials grant)
# ---------------------------------------------------------------------------

@dataclass
class _Token:
    access_token: str
    expires_at: float  # epoch seconds


class _TokenCache:
    """Thread-safe cache that fetches and refreshes the IDP JWT.

    The Elysia IDP is an AWS Cognito user pool. We use the standard OAuth2
    client_credentials grant: POST to `/oauth2/token` with HTTP Basic
    (`client_id:client_secret`) and `grant_type=client_credentials`.
    """

    def __init__(
        self,
        token_url: str,
        client_id: str,
        client_secret: str,
        scope: Optional[str] = None,
        skew_seconds: int = 60,
    ) -> None:
        self.token_url = token_url
        self.client_id = client_id
        self.client_secret = client_secret
        self.scope = scope
        self.skew_seconds = skew_seconds
        self._lock = threading.Lock()
        self._token: Optional[_Token] = None

    def get(self) -> str:
        with self._lock:
            if self._token and self._token.expires_at - time.time() > self.skew_seconds:
                return self._token.access_token
            self._token = self._fetch()
            return self._token.access_token

    def invalidate(self) -> None:
        with self._lock:
            self._token = None

    def _fetch(self) -> _Token:
        if not self.client_id or not self.client_secret:
            raise ElysiaAuthError(
                "ELYSIA_CLIENT_ID and ELYSIA_CLIENT_SECRET must be set "
                "to authenticate with the Elysia IDP."
            )

        form = {"grant_type": "client_credentials"}
        if self.scope:
            form["scope"] = self.scope
        body = urllib.parse.urlencode(form).encode()
        basic = base64.b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
            "Authorization": "Basic " + basic,
            "User-Agent": "PlannerPulse-Elysia/1.0",
        }
        req = urllib.request.Request(self.token_url, data=body, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            detail = (e.read() or b"").decode("utf-8", errors="replace")[:300]
            raise ElysiaAuthError(
                f"Token endpoint returned HTTP {e.code}: {detail}"
            ) from e
        except urllib.error.URLError as e:
            raise ElysiaAuthError(f"Token endpoint unreachable: {e.reason}") from e

        access = payload.get("access_token")
        expires_in = int(payload.get("expires_in", 3600))
        if not access:
            raise ElysiaAuthError(f"Token response missing access_token: {payload}")
        logger.info("Fetched fresh Elysia JWT (expires in %ds)", expires_in)
        return _Token(access_token=access, expires_at=time.time() + expires_in)


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------

class ElysiaError(Exception):
    """Base class for Elysia client errors."""


class ElysiaAuthError(ElysiaError):
    """OAuth2 / authentication problems."""


class ElysiaAPIError(ElysiaError):
    """Non-2xx response from the Elysia API."""

    def __init__(self, status: int, body: Any):
        self.status = status
        self.body = body
        super().__init__(f"Elysia API returned {status}: {str(body)[:300]}")


# ---------------------------------------------------------------------------
# OpenAI-compatible response objects (just enough fields to keep callers happy)
# ---------------------------------------------------------------------------

@dataclass
class _Message:
    role: str
    content: str


@dataclass
class _Choice:
    index: int
    message: _Message
    finish_reason: str = "stop"


@dataclass
class _Usage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


@dataclass
class _ChatCompletion:
    id: str
    model: str
    choices: List[_Choice]
    usage: _Usage = field(default_factory=_Usage)
    sources: List[str] = field(default_factory=list)  # Elysia-specific, kept around in case a caller wants it
    raw: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Prompt translation helpers
# ---------------------------------------------------------------------------

JSON_INSTRUCTION = (
    "\n\nIMPORTANT — RESPOND WITH ONLY A SINGLE VALID JSON OBJECT. "
    "Do not wrap the JSON in markdown code fences. Do not add commentary "
    "before or after the JSON. The first character of your response MUST "
    "be `{` and the last character MUST be `}`."
)


def _flatten_messages(messages: List[Dict[str, str]]) -> str:
    """Collapse OpenAI-style chat messages into Elysia's single `query` string.

    Roles are preserved with explicit headers so the model still sees system /
    user / assistant boundaries. Empty roles are normalised to "user".
    """
    parts: List[str] = []
    for m in messages:
        role = (m.get("role") or "user").strip().lower()
        content = (m.get("content") or "").strip()
        if not content:
            continue
        if role == "system":
            parts.append(f"[SYSTEM INSTRUCTIONS]\n{content}")
        elif role == "assistant":
            parts.append(f"[ASSISTANT]\n{content}")
        else:
            parts.append(f"[USER]\n{content}")
    return "\n\n".join(parts)


_JSON_OBJECT_RE = re.compile(r"\{.*\}", re.DOTALL)


def _coerce_json_string(text: str) -> str:
    """Best-effort cleanup of a model response when JSON mode was requested.

    Strips markdown code fences and any leading/trailing prose, returning the
    largest balanced `{...}` block we can find. Falls back to the original
    string if nothing better is recoverable.
    """
    if not text:
        return text
    s = text.strip()
    # Strip ```json ... ``` or ``` ... ```
    fence = re.match(r"^```(?:json)?\s*\n?(.*?)\n?```$", s, re.DOTALL)
    if fence:
        s = fence.group(1).strip()
    # Already a clean JSON object? Done.
    if s.startswith("{") and s.endswith("}"):
        return s
    # Greedy match the outermost { ... }
    m = _JSON_OBJECT_RE.search(s)
    if m:
        return m.group(0)
    return s


# ---------------------------------------------------------------------------
# Public Elysia client
# ---------------------------------------------------------------------------

class ElysiaClient:
    """Low-level Elysia API client.

    Most callers should use :func:`get_default_client` and the OpenAI-shim
    :class:`OpenAICompatClient` wrapper instead of constructing this directly.
    """

    def __init__(
        self,
        app_id: str,
        api_base: str = DEFAULT_API_BASE,
        token_cache: Optional[_TokenCache] = None,
        default_model: str = DEFAULT_MODEL,
        default_provider: str = DEFAULT_PROVIDER,
        default_collection: str = DEFAULT_COLLECTION,
        timeout: int = 90,
    ) -> None:
        self.app_id = app_id
        self.api_base = api_base.rstrip("/")
        self.token_cache = token_cache
        self.default_model = default_model
        self.default_provider = default_provider
        self.default_collection = default_collection
        self.timeout = timeout

    def chat_completion(
        self,
        *,
        query: str,
        model: Optional[str] = None,
        provider: Optional[str] = None,
        tokens: Optional[int] = None,
        chat_session: Optional[str] = None,
        collection: Optional[str] = None,
        output_type: str = DEFAULT_OUTPUT_TYPE,
        response_language: str = DEFAULT_LANGUAGE,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Call POST /v2/ai/chat/completion and return the parsed JSON body."""
        body: Dict[str, Any] = {
            "appId": self.app_id,
            "query": query,
            "name_of_model": model or self.default_model,
            "model": provider or self.default_provider,
            "chat_session": chat_session or str(uuid.uuid4()),
            "collection_name": collection or self.default_collection,
            "output_type": output_type,
            "response_language": response_language,
        }
        if tokens is not None:
            body["tokens"] = max(int(tokens), 65)  # spec: exclusiveMinimum 64
        if metadata:
            body["metadata"] = metadata

        return self._post_json(COMPLETION_PATH, body)

    # ---- internals ----

    def _headers(self) -> Dict[str, str]:
        h = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "PlannerPulse-Elysia/1.0",
        }
        if self.token_cache is not None:
            h["Authorization"] = "Bearer " + self.token_cache.get()
        return h

    def _post_json(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = self.api_base + path
        data = json.dumps(payload).encode("utf-8")

        # One automatic retry if the cached token has been invalidated server-side.
        for attempt in (1, 2):
            req = urllib.request.Request(url, data=data, headers=self._headers(), method="POST")
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    raw = resp.read().decode("utf-8")
                    return json.loads(raw) if raw else {}
            except urllib.error.HTTPError as e:
                detail = (e.read() or b"").decode("utf-8", errors="replace")
                # 401/403 + first attempt → refresh token and retry once.
                if e.code in (401, 403) and attempt == 1 and self.token_cache is not None:
                    logger.warning("Elysia returned %d; refreshing token and retrying.", e.code)
                    self.token_cache.invalidate()
                    continue
                try:
                    body = json.loads(detail)
                except Exception:
                    body = detail
                raise ElysiaAPIError(e.code, body) from e
            except urllib.error.URLError as e:
                raise ElysiaError(f"Elysia request failed: {e.reason}") from e

        # Should never reach here.
        raise ElysiaError("Unexpected retry loop exit")


# ---------------------------------------------------------------------------
# OpenAI-compatible facade
# ---------------------------------------------------------------------------

class _Completions:
    """Mimics `openai_client.chat.completions`."""

    def __init__(self, parent: "OpenAICompatClient"):
        self._parent = parent

    def create(
        self,
        *,
        model: str = DEFAULT_MODEL,
        messages: List[Dict[str, str]],
        response_format: Optional[Dict[str, str]] = None,
        temperature: Optional[float] = None,  # accepted, ignored — Elysia controls this
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> _ChatCompletion:
        """Drop-in replacement for `openai_client.chat.completions.create`."""
        if not messages:
            raise ValueError("messages must be a non-empty list")

        # Build the prompt
        query = _flatten_messages(messages)

        # JSON mode → append a strict instruction, parse the response after.
        json_mode = bool(response_format and response_format.get("type") == "json_object")
        if json_mode:
            query = query + JSON_INSTRUCTION

        elysia_model = _resolve_model(model)
        elysia_tokens = max_tokens if (max_tokens and max_tokens > 64) else None

        try:
            resp = self._parent._client.chat_completion(
                query=query,
                model=elysia_model,
                tokens=elysia_tokens,
            )
        except ElysiaError:
            raise
        except Exception as e:
            raise ElysiaError(f"Elysia call failed: {e}") from e

        answer = (resp.get("answer") or "").strip()
        sources = resp.get("sources") or []

        if json_mode:
            answer = _coerce_json_string(answer)

        completion = _ChatCompletion(
            id=str(uuid.uuid4()),
            model=elysia_model,
            choices=[_Choice(index=0, message=_Message(role="assistant", content=answer))],
            sources=sources,
            raw=resp,
        )
        return completion


class _Chat:
    def __init__(self, parent: "OpenAICompatClient"):
        self.completions = _Completions(parent)


class OpenAICompatClient:
    """Drop-in replacement for `openai.OpenAI`.

    PlannerPulse code does:

        client = OpenAI(api_key=...)
        client.chat.completions.create(model=..., messages=..., ...)

    Substitute this class and the same calls now hit Elysia.
    """

    def __init__(self, client: ElysiaClient):
        self._client = client
        self.chat = _Chat(self)

    # The OpenAI SDK exposes `.api_key` as a public attribute on the client.
    # We don't track keys but expose the property so `hasattr(client, 'api_key')`
    # checks (and any debug logging that prints client state) don't blow up.
    @property
    def api_key(self) -> Optional[str]:
        return None


# ---------------------------------------------------------------------------
# Module-level convenience factory
# ---------------------------------------------------------------------------

_DEFAULT_CLIENT: Optional[OpenAICompatClient] = None
_DEFAULT_CLIENT_LOCK = threading.Lock()


def _env(name: str, default: Optional[str] = None) -> Optional[str]:
    val = os.environ.get(name)
    return val.strip() if val else default


def get_default_client(refresh: bool = False) -> Optional[OpenAICompatClient]:
    """Return a cached singleton client built from environment variables.

    Returns None (and logs a warning) if the required env vars aren't set,
    so callers can degrade gracefully rather than crash at import time.
    """
    global _DEFAULT_CLIENT
    if _DEFAULT_CLIENT is not None and not refresh:
        return _DEFAULT_CLIENT

    with _DEFAULT_CLIENT_LOCK:
        if _DEFAULT_CLIENT is not None and not refresh:
            return _DEFAULT_CLIENT

        app_id = _env("ELYSIA_APP_ID")
        client_id = _env("ELYSIA_CLIENT_ID")
        client_secret = _env("ELYSIA_CLIENT_SECRET")
        token_url = _env("ELYSIA_TOKEN_URL", DEFAULT_TOKEN_URL)
        api_base = _env("ELYSIA_API_BASE", DEFAULT_API_BASE)
        scope = _env("ELYSIA_SCOPE")
        default_model = _env("ELYSIA_DEFAULT_MODEL", DEFAULT_MODEL)
        default_provider = _env("ELYSIA_DEFAULT_PROVIDER", DEFAULT_PROVIDER)
        default_collection = _env("ELYSIA_COLLECTION", DEFAULT_COLLECTION)

        missing = [
            name for name, val in (
                ("ELYSIA_APP_ID", app_id),
                ("ELYSIA_CLIENT_ID", client_id),
                ("ELYSIA_CLIENT_SECRET", client_secret),
            ) if not val
        ]
        if missing:
            logger.warning(
                "Elysia client not initialised — missing env vars: %s. "
                "LLM features will be disabled until these are set.",
                ", ".join(missing),
            )
            return None

        token_cache = _TokenCache(
            token_url=token_url,  # type: ignore[arg-type]
            client_id=client_id,  # type: ignore[arg-type]
            client_secret=client_secret,  # type: ignore[arg-type]
            scope=scope,
        )
        elysia = ElysiaClient(
            app_id=app_id,  # type: ignore[arg-type]
            api_base=api_base,  # type: ignore[arg-type]
            token_cache=token_cache,
            default_model=default_model,  # type: ignore[arg-type]
            default_provider=default_provider,  # type: ignore[arg-type]
            default_collection=default_collection,  # type: ignore[arg-type]
        )
        _DEFAULT_CLIENT = OpenAICompatClient(elysia)
        logger.info(
            "Elysia client ready (api=%s, app_id=%s, default_model=%s).",
            api_base, app_id, default_model,
        )
        return _DEFAULT_CLIENT


def is_configured() -> bool:
    """True iff the env vars required for the default client are present."""
    return all(_env(n) for n in ("ELYSIA_APP_ID", "ELYSIA_CLIENT_ID", "ELYSIA_CLIENT_SECRET"))


def test_connection() -> tuple[bool, str]:
    """Ping the Elysia API with a one-token completion and report status.

    Returns (ok, detail). Used by app.py's settings page.
    """
    client = get_default_client(refresh=True)
    if client is None:
        return False, "Elysia env vars not set"
    try:
        resp = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": "ping"}],
            max_tokens=65,
        )
        return True, f"Connected — model={resp.model}"
    except ElysiaAuthError as e:
        return False, f"Auth error: {e}"
    except ElysiaAPIError as e:
        return False, f"API error {e.status}: {e.body}"
    except Exception as e:
        return False, f"Error: {e}"
