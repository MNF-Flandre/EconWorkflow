from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass


@dataclass(frozen=True)
class LLMConfig:
    mode: str
    base_url: str
    model: str
    api_key_env: str
    temperature: float
    max_tokens: int


def _join_url(base_url: str, suffix: str) -> str:
    return f"{base_url.rstrip('/')}/{suffix.lstrip('/')}"


def _extract_text(content: object) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if not isinstance(item, dict):
                continue
            if item.get("type") in {"text", "output_text"}:
                text = item.get("text") or item.get("content") or ""
                if isinstance(text, str) and text.strip():
                    parts.append(text)
        return "\n\n".join(parts)
    return ""


def generate_response(config: LLMConfig, system_prompt: str, user_prompt: str) -> str:
    if config.mode != "openai-compatible":
        raise RuntimeError("当前 LLM 模式不是 openai-compatible，无法直接执行模型调用。")

    payload = {
        "model": config.model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": config.temperature,
        "max_tokens": config.max_tokens,
    }
    headers = {"Content-Type": "application/json"}
    api_key = os.environ.get(config.api_key_env, "").strip()
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    request = urllib.request.Request(
        _join_url(config.base_url, "/chat/completions"),
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"模型接口返回 HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"模型接口不可用: {exc.reason}") from exc

    data = json.loads(body)
    choices = data.get("choices") or []
    if not choices:
        raise RuntimeError("模型接口没有返回 choices。")
    message = choices[0].get("message") or {}
    content = _extract_text(message.get("content"))
    if not content:
        raise RuntimeError("模型接口返回了空内容。")
    return content
