from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEFAULT_FRIENDLI_BASE_URL = "https://api.friendli.ai/dedicated/v1"


@dataclass(frozen=True)
class FriendliConfig:
    api_key: str
    model: str
    chat_completions_url: str

    @classmethod
    def from_env(cls, env_file: Path | None = None) -> "FriendliConfig":
        values = load_dotenv_values(env_file) if env_file else {}
        env = {**values, **os.environ}
        base_url = env.get("FRIENDLI_BASE_URL", DEFAULT_FRIENDLI_BASE_URL)
        chat_url = env.get("FRIENDLI_CHAT_COMPLETIONS_URL") or (
            f"{base_url.rstrip('/')}/chat/completions"
        )
        return cls(
            api_key=env.get("FRIENDLI_API_KEY")
            or env.get("K_EXAONE_API_KEY")
            or "",
            model=env.get("K_EXAONE_ENDPOINT_ID")
            or env.get("FRIENDLI_ENDPOINT_ID")
            or env.get("K_EXAONE_MODEL")
            or "",
            chat_completions_url=chat_url,
        )

    @property
    def configured(self) -> bool:
        return bool(self.api_key and self.model)

    @property
    def missing(self) -> list[str]:
        missing = []
        if not self.api_key:
            missing.append("FRIENDLI_API_KEY")
        if not self.model:
            missing.append("K_EXAONE_ENDPOINT_ID")
        return missing

    def public_status(self) -> dict[str, Any]:
        return {
            "configured": self.configured,
            "hasApiKey": bool(self.api_key),
            "hasEndpointId": bool(self.model),
            "chatCompletionsUrl": self.chat_completions_url,
            "missing": self.missing,
        }


@dataclass(frozen=True)
class ChatResult:
    ok: bool
    http_status: int | str
    retry_after: str
    ms: int
    content: str
    reasoning: str = ""
    finish_reason: str = ""
    error: str = ""


@dataclass(frozen=True)
class StreamParseResult:
    content: str
    reasoning: str
    finish_reason: str


class FriendliClient:
    def __init__(self, config: FriendliConfig, timeout_sec: int = 180) -> None:
        if not config.configured:
            raise ValueError(f"Missing API configuration: {', '.join(config.missing)}")
        self.config = config
        self.timeout_sec = timeout_sec

    def chat(
        self,
        messages: list[dict[str, str]],
        *,
        max_tokens: int = 1400,
        temperature: float = 0,
        enable_thinking: bool = False,
        parse_reasoning: bool = True,
    ) -> ChatResult:
        started = time.perf_counter()
        payload = {
            "model": self.config.model,
            "messages": normalize_messages(messages),
            "stream": True,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "chat_template_kwargs": {"enable_thinking": enable_thinking},
            "parse_reasoning": parse_reasoning,
        }
        request = urllib.request.Request(
            self.config.chat_completions_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
                "Accept": "text/event-stream",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=self.timeout_sec) as response:
                raw = response.read().decode("utf-8", errors="replace")
                parsed = parse_openai_compatible_sse(raw)
                return ChatResult(
                    ok=200 <= response.status < 300,
                    http_status=response.status,
                    retry_after=response.headers.get("retry-after", ""),
                    ms=_elapsed_ms(started),
                    content=parsed.content,
                    reasoning=parsed.reasoning,
                    finish_reason=parsed.finish_reason,
                )
        except urllib.error.HTTPError as error:
            detail = _safe_error_body(error)
            return ChatResult(
                ok=False,
                http_status=error.code,
                retry_after=error.headers.get("retry-after", "") if error.headers else "",
                ms=_elapsed_ms(started),
                content="",
                error=detail,
            )
        except TimeoutError:
            return ChatResult(
                ok=False,
                http_status="TIMEOUT",
                retry_after="",
                ms=_elapsed_ms(started),
                content="",
                error=f"timeout after {self.timeout_sec}s",
            )
        except OSError as error:
            return ChatResult(
                ok=False,
                http_status="ERR",
                retry_after="",
                ms=_elapsed_ms(started),
                content="",
                error=str(error),
            )


def load_dotenv_values(path: Path | None) -> dict[str, str]:
    if path is None or not path.exists():
        return {}
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        value = value.strip().strip("'\"")
        if key:
            values[key] = value
    return values


def normalize_messages(messages: list[dict[str, str]]) -> list[dict[str, str]]:
    normalized: list[dict[str, str]] = []
    for message in messages:
        role = message.get("role", "")
        content = message.get("content", "")
        if role not in {"system", "user", "assistant"}:
            continue
        if not isinstance(content, str) or not content.strip():
            continue
        normalized.append({"role": role, "content": content.strip()})
    if not normalized:
        raise ValueError("At least one non-empty chat message is required.")
    return normalized


def parse_openai_compatible_sse(stream_text: str) -> StreamParseResult:
    content_parts: list[str] = []
    reasoning_parts: list[str] = []
    finish_reason = ""

    text = stream_text.strip()
    if text.startswith("{"):
        try:
            parsed = json.loads(text)
            choice = _first_choice(parsed)
            delta = choice.get("message") or choice.get("delta") or {}
            return StreamParseResult(
                content=_pick_text(delta.get("content")),
                reasoning=_pick_text(_pick_reasoning(delta)),
                finish_reason=str(choice.get("finish_reason") or ""),
            )
        except json.JSONDecodeError:
            pass

    for block in stream_text.splitlines():
        # Fast path for one-line SSE chunks produced by urllib read().
        if not block.startswith("data:"):
            continue
        data = block[5:].strip()
        if not data or data == "[DONE]":
            continue
        try:
            parsed = json.loads(data)
        except json.JSONDecodeError:
            content_parts.append(data)
            continue
        choice = _first_choice(parsed)
        delta = choice.get("delta") or choice.get("message") or {}
        content_parts.append(_pick_text(delta.get("content")))
        reasoning_parts.append(_pick_text(_pick_reasoning(delta)))
        if choice.get("finish_reason"):
            finish_reason = str(choice["finish_reason"])

    return StreamParseResult(
        content="".join(content_parts).strip(),
        reasoning="".join(reasoning_parts).strip(),
        finish_reason=finish_reason,
    )


def _first_choice(payload: dict[str, Any]) -> dict[str, Any]:
    choices = payload.get("choices")
    if isinstance(choices, list) and choices:
        choice = choices[0]
        if isinstance(choice, dict):
            return choice
    return {}


def _pick_reasoning(delta: dict[str, Any]) -> Any:
    return (
        delta.get("reasoning_content")
        or delta.get("reasoning")
        or delta.get("reasoningContent")
        or delta.get("thinking")
        or delta.get("thoughts")
    )


def _pick_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        parts = []
        for item in value:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                parts.append(str(item.get("text") or item.get("content") or ""))
        return "".join(parts)
    return ""


def _safe_error_body(error: urllib.error.HTTPError) -> str:
    try:
        text = error.read().decode("utf-8", errors="replace")
    except OSError:
        return error.reason or "HTTP error"
    if not text:
        return str(error.reason or "HTTP error")
    try:
        payload = json.loads(text)
        message = payload.get("error", {}).get("message") or payload.get("message")
        if message:
            return str(message)[:800]
    except json.JSONDecodeError:
        pass
    return " ".join(text.split())[:800]


def _elapsed_ms(started: float) -> int:
    return round((time.perf_counter() - started) * 1000)

