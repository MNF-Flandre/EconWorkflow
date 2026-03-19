from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

from econflow.core import find_workspace, is_builtin_role, load_config, slugify

PROCESS_TEMPLATES_FILE = "process_templates.json"
PROCESS_STATE_FILE = "process_state.json"

DEFAULT_PROCESS_TEMPLATES: dict[str, dict[str, Any]] = {
    "standard-research": {
        "id": "standard-research",
        "name": "标准研究流程",
        "summary": "适合从选题评估一路推进到成文整理的完整流程。",
        "is_builtin": True,
        "steps": [
            {
                "id": "phd-review",
                "label": "博士生评审",
                "summary": "先判断题目、数据和故事线是否站得住。",
            },
            {
                "id": "pi-decision",
                "label": "PI 决策",
                "summary": "决定继续推进、收窄范围还是暂时止损。",
            },
            {
                "id": "literature-data",
                "label": "文献与数据准备",
                "summary": "补文献、盘数据、明确样本与变量口径。",
            },
            {
                "id": "cleaning-regression",
                "label": "清洗与回归执行",
                "summary": "清洗样本、构造变量并推进基准结果。",
            },
            {
                "id": "replication-drafting",
                "label": "复核与成文整理",
                "summary": "复核结果、整理表图并形成成文提纲。",
            },
        ],
    },
}


def _templates_path(root: Path) -> Path:
    config = load_config(find_workspace(root))
    return config.shared_notes_dir / PROCESS_TEMPLATES_FILE


def _state_path(root: Path) -> Path:
    config = load_config(find_workspace(root))
    return config.shared_notes_dir / PROCESS_STATE_FILE


def _normalize_step(label: str, summary: str = "", used_ids: set[str] | None = None) -> dict[str, str]:
    used_ids = used_ids or set()
    base_id = slugify(label) or "step"
    step_id = base_id
    index = 2
    while step_id in used_ids:
        step_id = f"{base_id}-{index}"
        index += 1
    used_ids.add(step_id)
    return {
        "id": step_id,
        "label": label.strip(),
        "summary": summary.strip(),
    }


def parse_steps_text(raw_text: str) -> list[dict[str, str]]:
    steps: list[dict[str, str]] = []
    used_ids: set[str] = set()
    for raw_line in raw_text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        parts = [part.strip() for part in line.split("|", 1)]
        label = parts[0]
        summary = parts[1] if len(parts) > 1 else ""
        if not label:
            continue
        steps.append(_normalize_step(label, summary, used_ids))
    return steps


def parse_steps_payload(raw_json: str = "", raw_text: str = "") -> list[dict[str, str]]:
    raw_json = raw_json.strip()
    if raw_json:
        try:
            payload = json.loads(raw_json)
        except json.JSONDecodeError:
            payload = None
        if isinstance(payload, list):
            used_ids: set[str] = set()
            steps: list[dict[str, str]] = []
            for item in payload:
                if not isinstance(item, dict):
                    continue
                label = str(item.get("label", "")).strip()
                summary = str(item.get("summary", "")).strip()
                if not label:
                    continue
                steps.append(_normalize_step(label, summary, used_ids))
            if steps:
                return steps
    return parse_steps_text(raw_text)


def _sanitize_template(process_id: str, payload: dict[str, Any], *, builtin: bool) -> dict[str, Any] | None:
    name = str(payload.get("name", "")).strip()
    summary = str(payload.get("summary", "")).strip()
    raw_steps = payload.get("steps", [])
    if not name or not isinstance(raw_steps, list):
        return None
    used_ids: set[str] = set()
    steps: list[dict[str, str]] = []
    for raw_step in raw_steps:
        if not isinstance(raw_step, dict):
            continue
        label = str(raw_step.get("label", "")).strip()
        if not label:
            continue
        summary_text = str(raw_step.get("summary", "")).strip()
        raw_step_id = str(raw_step.get("id", "")).strip()
        if raw_step_id and raw_step_id not in used_ids:
            step_id = raw_step_id
            used_ids.add(step_id)
            steps.append({"id": step_id, "label": label, "summary": summary_text})
        else:
            steps.append(_normalize_step(label, summary_text, used_ids))
    if not steps:
        return None
    return {
        "id": process_id,
        "name": name,
        "summary": summary,
        "steps": steps,
        "is_builtin": builtin,
    }


def load_process_templates(root: Path | None = None) -> dict[str, dict[str, Any]]:
    workspace_root = find_workspace(root)
    merged = copy.deepcopy(DEFAULT_PROCESS_TEMPLATES)
    custom_path = _templates_path(workspace_root)
    if not custom_path.exists():
        return merged
    try:
        payload = json.loads(custom_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return merged
    if not isinstance(payload, dict):
        return merged
    for process_id, raw_template in payload.items():
        if not isinstance(raw_template, dict):
            continue
        normalized_id = slugify(str(process_id)) or ""
        if not normalized_id:
            continue
        template = _sanitize_template(normalized_id, raw_template, builtin=False)
        if template is None:
            continue
        merged[normalized_id] = template
    return merged


def save_custom_process(root: Path, *, process_id: str, name: str, summary: str, steps: list[dict[str, str]]) -> dict[str, Any]:
    workspace_root = find_workspace(root)
    normalized_id = slugify(process_id or name)
    if not normalized_id:
        raise RuntimeError("流程名称不能为空。")
    if normalized_id in DEFAULT_PROCESS_TEMPLATES:
        raise RuntimeError("默认流程不能直接覆盖。")
    template = _sanitize_template(
        normalized_id,
        {
            "name": name,
            "summary": summary,
            "steps": steps,
        },
        builtin=False,
    )
    if template is None:
        raise RuntimeError("流程至少需要一个步骤。")
    custom_path = _templates_path(workspace_root)
    custom_path.parent.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {}
    if custom_path.exists():
        try:
            existing = json.loads(custom_path.read_text(encoding="utf-8"))
            if isinstance(existing, dict):
                payload = existing
        except json.JSONDecodeError:
            payload = {}
    payload[normalized_id] = {
        "name": template["name"],
        "summary": template["summary"],
        "steps": template["steps"],
    }
    custom_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return template


def delete_custom_process(root: Path, process_id: str) -> None:
    workspace_root = find_workspace(root)
    normalized_id = slugify(process_id)
    if normalized_id in DEFAULT_PROCESS_TEMPLATES:
        raise RuntimeError("默认流程不能删除。")
    custom_path = _templates_path(workspace_root)
    payload: dict[str, Any] = {}
    if custom_path.exists():
        try:
            existing = json.loads(custom_path.read_text(encoding="utf-8"))
            if isinstance(existing, dict):
                payload = existing
        except json.JSONDecodeError:
            payload = {}
    payload.pop(normalized_id, None)
    if payload:
        custom_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    elif custom_path.exists():
        custom_path.unlink()
    current_id = current_process_id(workspace_root)
    if current_id == normalized_id:
        save_current_process_id(workspace_root, next(iter(load_process_templates(workspace_root).keys()), ""))


def default_process_id(root: Path | None = None) -> str:
    templates = load_process_templates(root)
    current_id = current_process_id(root)
    if current_id in templates:
        return current_id
    return next(iter(templates.keys()))


def current_process_id(root: Path | None = None) -> str:
    workspace_root = find_workspace(root)
    state_path = _state_path(workspace_root)
    if not state_path.exists():
        return ""
    try:
        payload = json.loads(state_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return ""
    if not isinstance(payload, dict):
        return ""
    return slugify(str(payload.get("current_process_id", "")).strip())


def save_current_process_id(root: Path | None, process_id: str) -> str:
    workspace_root = find_workspace(root)
    normalized_id = slugify(process_id)
    templates = load_process_templates(workspace_root)
    if normalized_id not in templates:
        raise RuntimeError("没有找到这套流程。")
    state_path = _state_path(workspace_root)
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(
        json.dumps({"current_process_id": normalized_id}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return normalized_id


def template_steps_text(template: dict[str, Any]) -> str:
    lines: list[str] = []
    for step in template.get("steps", []):
        label = str(step.get("label", "")).strip()
        summary = str(step.get("summary", "")).strip()
        if not label:
            continue
        lines.append(f"{label} | {summary}" if summary else label)
    return "\n".join(lines)
