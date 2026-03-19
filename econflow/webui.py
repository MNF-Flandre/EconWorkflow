from __future__ import annotations

import datetime as dt
import json
import os
import re
from pathlib import Path
from typing import Any

from flask import Flask, abort, flash, redirect, render_template, request, url_for

from econflow.core import (
    PIPELINES,
    create_custom_role,
    delete_project,
    delete_role,
    create_project,
    create_ticket,
    ensure_workspace,
    find_workspace,
    is_builtin_role,
    load_config,
    load_role_specs,
    run_pipeline,
    run_role,
    slugify,
)
from econflow.processes import (
    current_process_id,
    default_process_id,
    delete_custom_process,
    load_process_templates,
    parse_steps_payload,
    save_current_process_id,
    save_custom_process,
    template_steps_text,
)

SECRETS_FILE = ".webui-secrets.json"
UI_STATE_FILE = "ui_state.json"
AGENT_PROFILE_FILE = "profile.json"
AGENT_CARD_FILE = "card.md"
AGENT_ROLE_FILE = "role.md"
DEFAULT_STAGE = "discovery"
PROCESS_STEP_SUGGESTIONS: tuple[dict[str, str], ...] = (
    {"label": "第一阶段：创意发现", "summary": "检索文献、提炼研究缺口与假设，经挑战者独立审核，确认选题不重复且有支撑。"},
    {"label": "第二阶段：研究设计与锁定", "summary": "将假设转化为变量定义、样本边界与实证规格，经数据审计员确认可得性后正式锁定。"},
    {"label": "第三阶段：数据工程", "summary": "按锁定规格清洗合并数据，经质量审计检查样本流失与完整性，达标后方可推进。"},
    {"label": "第四阶段：实证执行", "summary": "按锁定规格跑基准回归，再经全套稳健性压力测试，结果通过方可进入最终阶段。"},
    {"label": "第五阶段：经济解释", "summary": "解释系数经济含义，模拟期刊审稿人批判性评审，产出最终报告与审计日志。"},
    {"label": "PI 决策", "summary": "审阅评审意见，决定继续推进、调整方向还是暂停课题。"},
    {"label": "文献补充", "summary": "补齐文献位置、边际贡献和相关机制。"},
    {"label": "数据盘点", "summary": "明确数据来源、样本范围和可得性。"},
    {"label": "稳健性检验", "summary": "补稳健性、安慰剂检验和异质性分析。"},
    {"label": "成文整理", "summary": "把图表、叙述和附录整理成草稿。"},
)
RESEARCH_STAGES = (
    {
        "id": "discovery",
        "label": "第一阶段：创意发现",
        "summary": "检索文献、提炼研究缺口与假设，经挑战者独立审核，确认选题不重复且有支撑。",
    },
    {
        "id": "design-lock",
        "label": "第二阶段：研究设计与锁定",
        "summary": "将假设转化为变量定义与实证规格，经数据审计员确认可得性后正式锁定，后续不可更改。",
    },
    {
        "id": "data-ops",
        "label": "第三阶段：数据工程",
        "summary": "按锁定规格清洗合并数据，经质量审计检查样本流失与完整性，达标后方可进入实证阶段。",
    },
    {
        "id": "econometrics",
        "label": "第四阶段：实证执行",
        "summary": "按锁定规格跑基准回归，再经全套稳健性压力测试，结果通过方可进入最终阶段。",
    },
    {
        "id": "synthesis",
        "label": "第五阶段：经济解释",
        "summary": "解释系数经济含义，模拟顶级期刊审稿人批判性评审，产出最终报告与全流程审计日志。",
    },
)
STAGE_OPTIONS = tuple(stage["id"] for stage in RESEARCH_STAGES)
DECISION_OPTIONS = (
    "继续推进",
    "退回重做",
    "暂停课题",
    "要求复议",
    "调整方向后推进",
)
STAGE_LABELS = {stage["id"]: stage["label"] for stage in RESEARCH_STAGES}
PIPELINE_LABELS = {
    "econ-os-2.0": "Econ-OS 2.0：5阶段自动化经济学研究",
    "committee-review": "博士生委员会评审",
    "ra-sprint": "硕士生执行推进",
    "faculty-lab": "全实验室联动",
}
AGENT_SKILL_DEFAULTS: dict[str, tuple[str, ...]] = {
    "b1_explorer": ("系统文献搜索", "综合相关研究", "结构化文献矩阵"),
    "b2_challenger": ("独立审查", "冲突证据检索", "研究重复性评估"),
    "c1_designer": ("假设映射", "变量定义", "规格冻结"),
    "c2_data_auditor": ("数据源验证", "口径一致性检查", "可得性评估"),
    "d1_engineer": ("数据清洗", "样本合并", "滞后结构化"),
    "d2_qa_auditor": ("数据质量审计", "缺失值分析", "合并覆盖率评估"),
    "e1_runner": ("基准回归执行", "固定效应设置", "聚类应用"),
    "e2_adversarial_auditor": ("稳健性压力测试", "异常值检验", "子样本分析"),
    "f1_narrator": ("系数经济学解释", "假设结果对比", "报告撰写"),
    "f2_journal_reviewer": ("期刊审稿模拟", "内生性检查", "学术质量评估"),
    "phd_feasibility": ("文献定位", "边际贡献判断", "投稿口径设计"),
    "phd_data": ("数据可得性评估", "识别策略审查", "变量口径设计"),
    "phd_story": ("故事线搭建", "审稿风险预判", "执行包拆解"),
    "ma_literature": ("文献检索", "文献矩阵整理", "相关研究归类"),
    "ma_data": ("数据清单梳理", "字段映射", "抓取与申请路径记录"),
    "ma_cleaning": ("数据清洗", "合并规则设计", "变量构造记录"),
    "ma_regression": ("回归执行", "表图规划", "稳健性方案整理"),
    "ma_replication": ("复核检查", "日志记录", "交付验收"),
}
REPORT_STYLE_DEFAULTS = {
    "phd": ("先给判断，再给理由。", "把风险和不确定点单独列清楚。", "给 PI 一个明确的下一步建议。"),
    "ma": ("先说明完成了什么，再说明还缺什么。", "所有输入材料和输出结果都要能追溯。", "对容易出错的步骤单独提醒。"),
    "econ-os": ("按照规格执行。", "记录所有关键决策点和数据质量检查。", "发现问题立即标记，不掩盖。"),
}


def _read_text(path: Path) -> str:
    if not path.exists():
        return ""
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="replace")


def _read_json(path: Path, default: dict[str, Any] | None = None) -> dict[str, Any]:
    if not path.exists():
        return default or {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default or {}


def _project_dir(root: Path, slug: str) -> Path:
    project_dir = load_config(root).projects_dir / slug
    if not project_dir.exists():
        raise FileNotFoundError(slug)
    return project_dir


def _project_title(project_dir: Path) -> str:
    brief = _read_text(project_dir / "brief.md")
    for line in brief.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return project_dir.name


def _strip_markdown(text: str) -> str:
    cleaned = re.sub(r"`([^`]*)`", r"\1", text)
    cleaned = re.sub(r"\[(.*?)\]\((.*?)\)", r"\1", cleaned)
    cleaned = re.sub(r"[*_>#-]{1,3}", " ", cleaned)
    cleaned = re.sub(r"\|", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip()


def _truncate(text: str, limit: int = 240) -> str:
    normalized = _strip_markdown(text)
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 1].rstrip() + "…"


def _extract_sections(markdown_text: str, limit: int = 3) -> list[dict[str, str]]:
    text = markdown_text.replace("\r\n", "\n").strip()
    if not text:
        return []
    matches = list(re.finditer(r"(?m)^##+\s+(.+)$", text))
    if not matches:
        return [{"heading": "摘要", "body": _truncate(text, 360)}]
    sections: list[dict[str, str]] = []
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        body = text[start:end].strip()
        if not body:
            continue
        sections.append({"heading": match.group(1).strip(), "body": _truncate(body, 360)})
        if len(sections) >= limit:
            break
    return sections


def _latest_run_for_role(project_dir: Path, role_id: str) -> Path | None:
    run_dirs = sorted((project_dir / "runs").glob(f"*_{role_id}"))
    return run_dirs[-1] if run_dirs else None


def _latest_run_metadata(run_dir: Path | None) -> dict[str, Any]:
    if run_dir is None:
        return {}
    return _read_json(run_dir / "metadata.json", default={})


def _load_ui_state(project_dir: Path) -> dict[str, Any]:
    workspace_root = project_dir.parent.parent
    role_specs = load_role_specs(workspace_root)
    process_templates = load_process_templates(workspace_root)
    state = _read_json(project_dir / UI_STATE_FILE, default={})
    active_roles = [role_id for role_id in state.get("active_roles", []) if role_id in role_specs]
    if not active_roles:
        econ_os_roles = [role_id for role_id, spec in role_specs.items() if spec.layer == "econ-os"]
        active_roles = econ_os_roles or list(role_specs.keys())
    decisions = state.get("pi_decisions", [])
    if not isinstance(decisions, list):
        decisions = []
    stage = state.get("stage", DEFAULT_STAGE)
    if stage not in STAGE_OPTIONS:
        stage = DEFAULT_STAGE
    process_id = str(state.get("process_id", "")).strip() or default_process_id(workspace_root)
    if process_id not in process_templates:
        process_id = default_process_id(workspace_root)
    process_template = process_templates[process_id]
    step_ids = [str(step.get("id", "")).strip() for step in process_template.get("steps", []) if str(step.get("id", "")).strip()]
    process_step = str(state.get("process_step", "")).strip()
    if process_step not in step_ids:
        process_step = step_ids[0] if step_ids else ""
    raw_assignments = state.get("process_assignments", {})
    if not isinstance(raw_assignments, dict):
        raw_assignments = {}
    process_assignments: dict[str, list[str]] = {}
    for step_id in step_ids:
        assigned_roles = raw_assignments.get(step_id, [])
        if not isinstance(assigned_roles, list):
            assigned_roles = []
        process_assignments[step_id] = [role_id for role_id in assigned_roles if role_id in role_specs]
    return {
        "active_roles": active_roles,
        "stage": stage,
        "pi_decisions": decisions,
        "process_id": process_id,
        "process_step": process_step,
        "process_assignments": process_assignments,
    }


def _save_ui_state(project_dir: Path, state: dict[str, Any]) -> None:
    (project_dir / UI_STATE_FILE).write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def _project_metrics(project_dir: Path) -> dict[str, int | str]:
    outputs = list((project_dir / "outputs").glob("*.md"))
    open_tickets = [
        path for path in (project_dir / "tickets" / "open").glob("*.md") if path.name.lower() != "readme.md"
    ]
    runs = sorted([path for path in (project_dir / "runs").glob("*") if path.is_dir()])
    return {
        "outputs": len(outputs),
        "open_tickets": len(open_tickets),
        "runs": len(runs),
        "latest_run": runs[-1].name if runs else "",
    }


def _load_project_cards(project_dir: Path, active_roles: list[str]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {"phd": [], "ma": [], "econ-os": []}
    for role_id, spec in load_role_specs(project_dir.parent.parent).items():
        deliverable_path = project_dir / spec.deliverable
        deliverable_text = _read_text(deliverable_path)
        latest_run = _latest_run_for_role(project_dir, role_id)
        metadata = _latest_run_metadata(latest_run)
        if spec.layer not in grouped:
            grouped[spec.layer] = []
        grouped[spec.layer].append(
            {
                "role_id": role_id,
                "name": spec.name,
                "default_task": spec.default_task,
                "active": role_id in active_roles,
                "deliverable_path": spec.deliverable,
                "deliverable_ready": deliverable_path.exists() and "待生成" not in deliverable_text,
                "latest_run": latest_run.name if latest_run else "",
                "latest_prompt_path": str((latest_run / "prompt.md").relative_to(project_dir)) if latest_run else "",
                "latest_response_path": (
                    str((latest_run / "response.md").relative_to(project_dir))
                    if latest_run and (latest_run / "response.md").exists()
                    else ""
                ),
                "context_files": metadata.get("context", []),
                "latest_task": metadata.get("task", spec.default_task),
                "sections": _extract_sections(deliverable_text, limit=3),
                "excerpt": _truncate(deliverable_text, 280) if deliverable_text else "",
            }
        )
    return grouped


def _load_runs(project_dir: Path, limit: int = 12) -> list[dict[str, Any]]:
    runs = sorted([path for path in (project_dir / "runs").glob("*") if path.is_dir()], reverse=True)[:limit]
    items: list[dict[str, Any]] = []
    for run_dir in runs:
        metadata = _latest_run_metadata(run_dir)
        items.append(
            {
                "name": run_dir.name,
                "role_id": metadata.get("role", ""),
                "task": metadata.get("task", ""),
                "executed": bool(metadata.get("executed")),
                "context": metadata.get("context", []),
                "prompt_path": str((run_dir / "prompt.md").relative_to(project_dir)),
                "response_path": (
                    str((run_dir / "response.md").relative_to(project_dir)) if (run_dir / "response.md").exists() else ""
                ),
            }
        )
    return items


def _load_tickets(project_dir: Path) -> list[dict[str, str]]:
    tickets = sorted(
        [path for path in (project_dir / "tickets" / "open").glob("*.md") if path.name.lower() != "readme.md"],
        reverse=True,
    )
    items: list[dict[str, str]] = []
    for ticket_path in tickets:
        content = _read_text(ticket_path)
        title = ticket_path.stem
        for line in content.splitlines():
            if line.startswith("# "):
                title = line[2:].strip()
                break
        items.append(
            {
                "title": title,
                "path": str(ticket_path.relative_to(project_dir)),
                "excerpt": _truncate(content, 240),
            }
        )
    return items


def _project_process_view(root: Path, state: dict[str, Any]) -> dict[str, Any]:
    templates = load_process_templates(root)
    selected = templates[state["process_id"]]
    role_specs = load_role_specs(root)
    steps: list[dict[str, Any]] = []
    for step in selected.get("steps", []):
        step_id = str(step.get("id", "")).strip()
        assigned_ids = [role_id for role_id in state["process_assignments"].get(step_id, []) if role_id in role_specs]
        steps.append(
            {
                "id": step_id,
                "label": step.get("label", ""),
                "summary": step.get("summary", ""),
                "assigned_role_ids": assigned_ids,
                "assigned_roles": [role_specs[role_id].name for role_id in assigned_ids],
                "assigned_count": len(assigned_ids),
                "is_current": step_id == state["process_step"],
            }
        )
    return {
        "templates": list(templates.values()),
        "selected": selected,
        "steps": steps,
        "current_step": next((step for step in steps if step["id"] == state["process_step"]), steps[0] if steps else None),
    }


def _workspace_projects(root: Path) -> list[dict[str, Any]]:
    config = load_config(root)
    projects = []
    for project_dir in sorted([path for path in config.projects_dir.iterdir() if path.is_dir()], key=lambda item: item.name):
        metrics = _project_metrics(project_dir)
        state = _load_ui_state(project_dir)
        process_templates = load_process_templates(root)
        process_template = process_templates.get(state["process_id"], next(iter(process_templates.values())))
        projects.append(
            {
                "slug": project_dir.name,
                "title": _project_title(project_dir),
                "brief_excerpt": _truncate(_read_text(project_dir / "brief.md"), 260),
                "stage": state["stage"],
                "process_name": process_template["name"],
                "process_step": state["process_step"],
                "active_roles": len(state["active_roles"]),
                **metrics,
            }
        )
    return projects


def _workspace_process_cards(root: Path) -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = []
    for template in load_process_templates(root).values():
        cards.append(
            {
                **template,
                "steps_text": template_steps_text(template),
                "step_count": len(template.get("steps", [])),
            }
        )
    return cards


def _workspace_process_step_library(root: Path) -> list[dict[str, str]]:
    seen: set[tuple[str, str]] = set()
    items: list[dict[str, str]] = []
    for suggestion in PROCESS_STEP_SUGGESTIONS:
        key = (suggestion["label"], suggestion["summary"])
        if key in seen:
            continue
        seen.add(key)
        items.append({"label": suggestion["label"], "summary": suggestion["summary"]})
    for template in load_process_templates(root).values():
        for step in template.get("steps", []):
            label = str(step.get("label", "")).strip()
            summary = str(step.get("summary", "")).strip()
            if not label:
                continue
            key = (label, summary)
            if key in seen:
                continue
            seen.add(key)
            items.append({"label": label, "summary": summary})
    return items


def _load_secrets(root: Path) -> dict[str, str]:
    data = _read_json(root / SECRETS_FILE, default={})
    env_name = str(data.get("api_key_env", "")).strip()
    api_key = str(data.get("api_key", "")).strip()
    if env_name and api_key:
        os.environ[env_name] = api_key
    return {"api_key_env": env_name, "api_key": api_key}


def _save_secrets(root: Path, api_key_env: str, api_key: str) -> None:
    (root / SECRETS_FILE).write_text(
        json.dumps({"api_key_env": api_key_env, "api_key": api_key}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    if api_key_env and api_key:
        os.environ[api_key_env] = api_key


def _mask_secret(secret: str) -> str:
    if not secret:
        return ""
    if len(secret) <= 8:
        return "*" * len(secret)
    return f"{secret[:4]}{'*' * (len(secret) - 8)}{secret[-4:]}"


def _toml_value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return str(value)
    escaped = str(value).replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def _update_llm_config(root: Path, updates: dict[str, Any]) -> None:
    config_path = root / "workflow.toml"
    lines = config_path.read_text(encoding="utf-8").splitlines()
    section_start = None
    section_end = len(lines)
    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped == "[llm]":
            section_start = index
            continue
        if section_start is not None and stripped.startswith("[") and stripped.endswith("]"):
            section_end = index
            break
    if section_start is None:
        lines.extend(["", "[llm]"])
        section_start = len(lines) - 1
        section_end = len(lines)
    block = lines[section_start + 1 : section_end]
    positions: dict[str, int] = {}
    for index, line in enumerate(block):
        match = re.match(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=", line)
        if match:
            positions[match.group(1)] = index
    for key, value in updates.items():
        rendered = f"{key} = {_toml_value(value)}"
        if key in positions:
            block[positions[key]] = rendered
        else:
            block.append(rendered)
    new_lines = lines[: section_start + 1] + block + lines[section_end:]
    config_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")


def _resolve_project_path(project_dir: Path, relative_path: str) -> Path:
    candidate = (project_dir / relative_path).resolve()
    project_root = project_dir.resolve()
    if candidate != project_root and project_root not in candidate.parents:
        raise ValueError(relative_path)
    return candidate


def _split_lines(raw_text: str) -> list[str]:
    items: list[str] = []
    for line in raw_text.splitlines():
        cleaned = re.sub(r"^\s*(?:[-*•]|\d+\.)\s*", "", line).strip()
        if cleaned:
            items.append(cleaned)
    return items


def _extract_lead_paragraph(markdown_text: str) -> str:
    chunks = [chunk.strip() for chunk in markdown_text.replace("\r\n", "\n").split("\n\n")]
    for chunk in chunks:
        if chunk and not chunk.startswith("#"):
            return _strip_markdown(chunk)
    return ""


def _extract_markdown_list(markdown_text: str, heading: str) -> list[str]:
    pattern = rf"(?ms)^##+\s+{re.escape(heading)}\s*\n(.*?)(?=^##+\s+|\Z)"
    match = re.search(pattern, markdown_text)
    if not match:
        return []
    return _split_lines(match.group(1))


def _agent_profile_path(root: Path, role_id: str) -> Path:
    config = load_config(root)
    return config.agents_dir / role_id / AGENT_PROFILE_FILE


def _default_agent_profile(root: Path, role_id: str) -> dict[str, Any]:
    spec = load_role_specs(root)[role_id]
    config = load_config(root)
    role_text = _read_text(config.agents_dir / role_id / "role.md")
    memory_text = _read_text(config.agents_dir / role_id / "memory.md")
    responsibilities = _extract_markdown_list(role_text, "你的工作") or _extract_markdown_list(role_text, "你的职责")
    report_style = _extract_markdown_list(role_text, "你的汇报风格")
    return {
        "role_id": role_id,
        "name": spec.name,
        "layer": spec.layer,
        "is_builtin": is_builtin_role(role_id),
        "is_custom": not is_builtin_role(role_id),
        "mission": _extract_lead_paragraph(role_text) or spec.default_task,
        "responsibilities": responsibilities or [spec.default_task],
        "skills": list(AGENT_SKILL_DEFAULTS.get(role_id, ())),
        "report_style": report_style or list(REPORT_STYLE_DEFAULTS[spec.layer]),
        "deliverable": spec.deliverable,
        "deliverable_label": Path(spec.deliverable).name,
        "memory_excerpt": _truncate(memory_text, 220),
    }


def _load_agent_profile(root: Path, role_id: str) -> dict[str, Any]:
    profile = _default_agent_profile(root, role_id)
    stored = _read_json(_agent_profile_path(root, role_id), default={})
    mission = str(stored.get("mission", "")).strip()
    responsibilities = stored.get("responsibilities", [])
    skills = stored.get("skills", [])
    report_style = stored.get("report_style", [])
    if mission:
        profile["mission"] = mission
    if isinstance(responsibilities, list) and responsibilities:
        profile["responsibilities"] = [str(item).strip() for item in responsibilities if str(item).strip()]
    if isinstance(skills, list) and skills:
        profile["skills"] = [str(item).strip() for item in skills if str(item).strip()]
    if isinstance(report_style, list) and report_style:
        profile["report_style"] = [str(item).strip() for item in report_style if str(item).strip()]
    profile["responsibilities_text"] = "\n".join(profile["responsibilities"])
    profile["skills_text"] = "\n".join(profile["skills"])
    profile["report_style_text"] = "\n".join(profile["report_style"])
    profile["summary"] = _truncate(profile["mission"], 120)
    return profile


def _render_role_card(profile: dict[str, Any]) -> str:
    responsibilities = profile.get("responsibilities") or ["待补充"]
    skills = profile.get("skills") or ["待补充"]
    report_style = profile.get("report_style") or ["待补充"]
    responsibility_lines = "\n".join(f"{index}. {item}" for index, item in enumerate(responsibilities, start=1))
    skill_lines = "\n".join(f"- {item}" for item in skills)
    report_lines = "\n".join(f"- {item}" for item in report_style)
    layer_label = {
        "phd": "博士生评审层",
        "ma": "硕士生执行层",
        "econ-os": "Econ-OS 2.0 研究角色",
    }.get(profile.get("layer"), str(profile.get("layer") or ""))
    return (
        f"# {profile['name']}\n\n"
        f"{profile['mission'].strip() or '你是这个研究流程中的成员。'}\n\n"
        "## 你的职责\n\n"
        f"{responsibility_lines}\n\n"
        "## 你的技能\n\n"
        f"{skill_lines}\n\n"
        "## 你的汇报风格\n\n"
        f"{report_lines}\n\n"
        "## 交付重点\n\n"
        f"- 当前交付文件：`{profile['deliverable']}`\n"
        f"- 所属层级：{layer_label}\n"
    )


def _save_agent_profile(root: Path, role_id: str, *, mission: str, responsibilities: list[str], skills: list[str], report_style: list[str]) -> None:
    role_specs = load_role_specs(root)
    if role_id not in role_specs:
        raise RuntimeError(f"未知角色: {role_id}")
    profile = _load_agent_profile(root, role_id)
    profile["mission"] = mission.strip() or profile["mission"]
    profile["responsibilities"] = responsibilities or profile["responsibilities"]
    profile["skills"] = skills or profile["skills"]
    profile["report_style"] = report_style or profile["report_style"]
    payload = {
        "mission": profile["mission"],
        "responsibilities": profile["responsibilities"],
        "skills": profile["skills"],
        "report_style": profile["report_style"],
    }
    profile_path = _agent_profile_path(root, role_id)
    profile_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    config = load_config(root)
    (config.agents_dir / role_id / "role.md").write_text(_render_role_card(profile), encoding="utf-8")


def _joined_lines(items: list[str], fallback: str = "待补充") -> str:
    cleaned = [item.strip() for item in items if item.strip()]
    if not cleaned:
        return fallback
    return "；".join(cleaned[:3])


def _agent_card_path(root: Path, role_id: str) -> Path:
    config = load_config(root)
    return config.agents_dir / role_id / AGENT_CARD_FILE


def _agent_role_path(root: Path, role_id: str) -> Path:
    config = load_config(root)
    return config.agents_dir / role_id / AGENT_ROLE_FILE


def _default_agent_profile_ui(root: Path, role_id: str) -> dict[str, Any]:
    spec = load_role_specs(root)[role_id]
    config = load_config(root)
    role_text = _read_text(_agent_role_path(root, role_id))
    card_text = _read_text(_agent_card_path(root, role_id))
    memory_text = _read_text(config.agents_dir / role_id / "memory.md")
    responsibilities = _extract_markdown_list(role_text, "你的职责") or _extract_markdown_list(role_text, "你的工作")
    skills = _extract_markdown_list(role_text, "你的技能")
    report_style = _extract_markdown_list(role_text, "你的汇报方式")
    display_function = (
        _extract_markdown_list(card_text, "角色主要职能")
        or _extract_markdown_list(card_text, "主要职能")
        or responsibilities[:3]
        or [spec.default_task]
    )
    display_ability = (
        _extract_markdown_list(card_text, "角色主要能力")
        or _extract_markdown_list(card_text, "主要能力")
        or skills[:3]
        or list(AGENT_SKILL_DEFAULTS.get(role_id, ()))[:3]
        or ["待补充"]
    )
    return {
        "role_id": role_id,
        "name": spec.name,
        "layer": spec.layer,
        "is_builtin": is_builtin_role(role_id),
        "is_custom": not is_builtin_role(role_id),
        "mission": _extract_lead_paragraph(role_text) or spec.default_task,
        "responsibilities": responsibilities or [spec.default_task],
        "skills": skills or list(AGENT_SKILL_DEFAULTS.get(role_id, ())),
        "report_style": report_style or list(REPORT_STYLE_DEFAULTS[spec.layer]),
        "display_function": display_function[:3],
        "display_ability": display_ability[:3],
        "deliverable": spec.deliverable,
        "deliverable_label": Path(spec.deliverable).name,
        "memory_excerpt": _truncate(memory_text, 220),
    }


def _load_agent_profile_ui(root: Path, role_id: str) -> dict[str, Any]:
    profile = _default_agent_profile_ui(root, role_id)
    stored = _read_json(_agent_profile_path(root, role_id), default={})
    mission = str(stored.get("mission", "")).strip()
    responsibilities = stored.get("responsibilities", [])
    skills = stored.get("skills", [])
    report_style = stored.get("report_style", [])
    display_function = stored.get("display_function", [])
    display_ability = stored.get("display_ability", [])
    if mission:
        profile["mission"] = mission
    if isinstance(responsibilities, list) and responsibilities:
        profile["responsibilities"] = [str(item).strip() for item in responsibilities if str(item).strip()]
    if isinstance(skills, list) and skills:
        profile["skills"] = [str(item).strip() for item in skills if str(item).strip()]
    if isinstance(report_style, list) and report_style:
        profile["report_style"] = [str(item).strip() for item in report_style if str(item).strip()]
    if isinstance(display_function, list) and display_function:
        profile["display_function"] = [str(item).strip() for item in display_function if str(item).strip()]
    if isinstance(display_ability, list) and display_ability:
        profile["display_ability"] = [str(item).strip() for item in display_ability if str(item).strip()]
    profile["responsibilities_text"] = "\n".join(profile["responsibilities"])
    profile["skills_text"] = "\n".join(profile["skills"])
    profile["report_style_text"] = "\n".join(profile["report_style"])
    profile["display_function_text"] = _joined_lines(profile["display_function"])
    profile["display_ability_text"] = _joined_lines(profile["display_ability"])
    profile["display_function_textarea"] = "\n".join(profile["display_function"])
    profile["display_ability_textarea"] = "\n".join(profile["display_ability"])
    return profile


def _render_agent_display_card(profile: dict[str, Any]) -> str:
    display_function = profile.get("display_function") or ["待补充"]
    display_ability = profile.get("display_ability") or ["待补充"]
    function_lines = "\n".join(f"- {item}" for item in display_function)
    ability_lines = "\n".join(f"- {item}" for item in display_ability)
    return (
        f"# {profile['name']}\n\n"
        "## 角色主要职能\n\n"
        f"{function_lines}\n\n"
        "## 角色主要能力\n\n"
        f"{ability_lines}\n"
    )


def _render_agent_internal_role(profile: dict[str, Any]) -> str:
    responsibilities = profile.get("responsibilities") or ["待补充"]
    skills = profile.get("skills") or ["待补充"]
    report_style = profile.get("report_style") or ["待补充"]
    responsibility_lines = "\n".join(f"{index}. {item}" for index, item in enumerate(responsibilities, start=1))
    skill_lines = "\n".join(f"- {item}" for item in skills)
    report_lines = "\n".join(f"- {item}" for item in report_style)
    mission = profile.get("mission", "").strip() or "你是这个研究流程中的成员。"
    return (
        f"# {profile['name']}\n\n"
        f"{mission}\n\n"
        "## 你的职责\n\n"
        f"{responsibility_lines}\n\n"
        "## 你的技能\n\n"
        f"{skill_lines}\n\n"
        "## 你的汇报方式\n\n"
        f"{report_lines}\n"
    )


def _save_agent_profile_ui(
    root: Path,
    role_id: str,
    *,
    display_function: list[str],
    display_ability: list[str],
    mission: str,
    responsibilities: list[str],
    skills: list[str],
    report_style: list[str],
) -> None:
    role_specs = load_role_specs(root)
    if role_id not in role_specs:
        raise RuntimeError(f"未知角色: {role_id}")
    profile = _load_agent_profile_ui(root, role_id)
    profile["display_function"] = display_function or profile["display_function"]
    profile["display_ability"] = display_ability or profile["display_ability"]
    profile["mission"] = mission.strip() or profile["mission"]
    profile["responsibilities"] = responsibilities or profile["responsibilities"]
    profile["skills"] = skills or profile["skills"]
    profile["report_style"] = report_style or profile["report_style"]
    payload = {
        "display_function": profile["display_function"],
        "display_ability": profile["display_ability"],
        "mission": profile["mission"],
        "responsibilities": profile["responsibilities"],
        "skills": profile["skills"],
        "report_style": profile["report_style"],
    }
    profile_path = _agent_profile_path(root, role_id)
    profile_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    _agent_card_path(root, role_id).write_text(_render_agent_display_card(profile), encoding="utf-8")
    _agent_role_path(root, role_id).write_text(_render_agent_internal_role(profile), encoding="utf-8")


def _load_people_groups(root: Path) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {"econ-os": []}
    for role_id, spec in load_role_specs(root).items():
        if spec.layer not in grouped:
            grouped[spec.layer] = []
        grouped[spec.layer].append(_load_agent_profile_ui(root, role_id))
    return grouped


def _stage_sections(root: Path) -> list[dict[str, Any]]:
    projects = _workspace_projects(root)
    grouped: dict[str, list[dict[str, Any]]] = {stage["id"]: [] for stage in RESEARCH_STAGES}
    for project in projects:
        grouped.setdefault(str(project["stage"]), []).append(project)
    sections: list[dict[str, Any]] = []
    for stage in RESEARCH_STAGES:
        sections.append(
            {
                "id": stage["id"],
                "label": stage["label"],
                "summary": stage["summary"],
                "count": len(grouped.get(stage["id"], [])),
                "projects": grouped.get(stage["id"], []),
            }
        )
    return sections


def create_app(root: Path | None = None) -> Flask:
    workspace_root = find_workspace(root)
    app = Flask(
        __name__,
        template_folder=str(Path(__file__).with_name("templates")),
        static_folder=str(Path(__file__).with_name("static")),
    )
    app.config["SECRET_KEY"] = "econflow-local-webui"

    _load_secrets(workspace_root)

    @app.before_request
    def refresh_runtime_secrets() -> None:
        _load_secrets(workspace_root)

    @app.context_processor
    def inject_globals() -> dict[str, Any]:
        config = load_config(workspace_root)
        secrets = _load_secrets(workspace_root)
        api_key = os.environ.get(config.llm.api_key_env, "") or secrets.get("api_key", "")
        llm_ready = config.llm.mode == "openai-compatible" and bool(api_key)
        role_specs = load_role_specs(workspace_root)
        return {
            "workspace_root": str(workspace_root),
            "role_specs": role_specs,
            "pipeline_specs": PIPELINES,
            "pipeline_labels": PIPELINE_LABELS,
            "stage_options": STAGE_OPTIONS,
            "stage_labels": STAGE_LABELS,
            "decision_options": DECISION_OPTIONS,
            "research_stages": RESEARCH_STAGES,
            "llm_config": config.llm,
            "llm_ready": llm_ready,
            "api_key_masked": _mask_secret(api_key),
            "current_process_id": default_process_id(workspace_root),
        }

    @app.get("/")
    def index() -> str:
        return render_template(
            "index.html",
            projects=_workspace_projects(workspace_root),
            stage_sections=_stage_sections(workspace_root),
        )

    @app.get("/research")
    def research_overview() -> str:
        return render_template(
            "index.html",
            projects=_workspace_projects(workspace_root),
            stage_sections=_stage_sections(workspace_root),
        )

    @app.get("/settings/processes")
    def process_settings() -> str:
        return render_template(
            "settings_processes.html",
            process_templates=_workspace_process_cards(workspace_root),
            process_step_library=_workspace_process_step_library(workspace_root),
            selected_process_id=default_process_id(workspace_root),
        )

    @app.post("/settings/processes")
    def save_process_template_from_ui() -> Any:
        process_name = request.form.get("name", "").strip()
        process_id = request.form.get("process_id", "").strip()
        summary = request.form.get("summary", "").strip()
        steps_json = request.form.get("steps_json", "")
        steps_text = request.form.get("steps", "").strip()
        steps = parse_steps_payload(steps_json, steps_text)
        if not process_name:
            flash("请先填写流程名称。", "error")
            return redirect(f"{url_for('process_settings')}#process-builder")
        if not steps:
            flash("请至少写一个流程步骤。", "error")
            return redirect(f"{url_for('process_settings')}#process-builder")
        try:
            template = save_custom_process(
                workspace_root,
                process_id=process_id or process_name,
                name=process_name,
                summary=summary,
                steps=steps,
            )
        except Exception as exc:  # noqa: BLE001
            flash(f"保存流程失败：{exc}", "error")
            return redirect(f"{url_for('process_settings')}#process-builder")
        flash(f"{template['name']} 已加入流程配置。", "success")
        return redirect(f"{url_for('process_settings')}#process-builder")

    @app.post("/settings/processes/current")
    def set_current_process_from_ui() -> Any:
        process_id = request.form.get("process_id", "").strip()
        if not process_id:
            flash("请先选择一套流程。", "error")
            return redirect(url_for("process_settings"))
        try:
            save_current_process_id(workspace_root, process_id)
        except Exception as exc:  # noqa: BLE001
            flash(f"设为当前流程失败：{exc}", "error")
            return redirect(url_for("process_settings"))
        flash("当前流程已更新。", "success")
        return redirect(url_for("process_settings"))

    @app.post("/settings/processes/<process_id>/delete")
    def delete_process_template_from_ui(process_id: str) -> Any:
        try:
            delete_custom_process(workspace_root, process_id)
        except Exception as exc:  # noqa: BLE001
            flash(f"删除流程失败：{exc}", "error")
            return redirect(url_for("process_settings"))
        flash("流程已删除。", "success")
        return redirect(url_for("process_settings"))

    @app.get("/settings/api")
    def api_settings() -> str:
        return render_template("settings_api.html")

    @app.get("/settings/people")
    def people_settings() -> str:
        return render_template("settings_people.html", people_groups=_load_people_groups(workspace_root))

    @app.post("/settings/people")
    def create_people_profile() -> Any:
        name = request.form.get("name", "").strip()
        role_id = request.form.get("role_id", "").strip()
        layer = request.form.get("layer", "econ-os").strip().lower() or "econ-os"
        display_function = _split_lines(request.form.get("display_function", ""))
        display_ability = _split_lines(request.form.get("display_ability", ""))
        mission = request.form.get("mission", "").strip()
        default_task = request.form.get("default_task", "").strip() or mission
        responsibilities = _split_lines(request.form.get("responsibilities", ""))
        skills = _split_lines(request.form.get("skills", ""))
        report_style = _split_lines(request.form.get("report_style", ""))
        context_files = tuple(_split_lines(request.form.get("context_files", "")) or ["brief.md"])
        if not name:
            flash("请先填写角色名称。", "error")
            return redirect(url_for("people_settings"))
        try:
            spec = create_custom_role(
                workspace_root,
                role_id=role_id or name,
                name=name,
                layer=layer,
                default_task=default_task,
                context_files=context_files,
            )
            created_role_id = slugify(role_id or name)
            _save_agent_profile_ui(
                workspace_root,
                created_role_id,
                display_function=display_function or [default_task or "待补充"],
                display_ability=display_ability or skills[:3] or ["待补充"],
                mission=mission or f"你是研究流程中的新成员，负责 {name} 相关工作。",
                responsibilities=responsibilities or [default_task or "按项目要求完成本轮任务。"],
                skills=skills or ["待补充"],
                report_style=report_style or ["先说明判断，再说明原因。"],
            )
        except Exception as exc:  # noqa: BLE001
            flash(f"新建角色失败：{exc}", "error")
            return redirect(url_for("people_settings"))
        flash(f"{spec.name} 已加入成员列表。", "success")
        return redirect(f"{url_for('people_settings')}#{created_role_id}")

    @app.post("/settings/people/<role_id>")
    def save_people_profile(role_id: str) -> Any:
        role_specs = load_role_specs(workspace_root)
        if role_id not in role_specs:
            abort(404)
        display_function = _split_lines(request.form.get("display_function", ""))
        display_ability = _split_lines(request.form.get("display_ability", ""))
        mission = request.form.get("mission", "").strip()
        responsibilities = _split_lines(request.form.get("responsibilities", ""))
        skills = _split_lines(request.form.get("skills", ""))
        report_style = _split_lines(request.form.get("report_style", ""))
        _save_agent_profile_ui(
            workspace_root,
            role_id,
            display_function=display_function,
            display_ability=display_ability,
            mission=mission,
            responsibilities=responsibilities,
            skills=skills,
            report_style=report_style,
        )
        flash(f"{role_specs[role_id].name} 的设置已更新。", "success")
        return redirect(f"{url_for('people_settings')}#{role_id}")

    @app.post("/settings/people/<role_id>/delete")
    def delete_people_profile(role_id: str) -> Any:
        role_specs = load_role_specs(workspace_root)
        if role_id not in role_specs:
            abort(404)
        try:
            delete_role(workspace_root, role_id)
            config = load_config(workspace_root)
            for project_dir in [path for path in config.projects_dir.iterdir() if path.is_dir()]:
                state = _load_ui_state(project_dir)
                state["active_roles"] = [item for item in state["active_roles"] if item != role_id]
                state["process_assignments"] = {
                    step_id: [item for item in assigned if item != role_id]
                    for step_id, assigned in state.get("process_assignments", {}).items()
                }
                _save_ui_state(project_dir, state)
        except Exception as exc:  # noqa: BLE001
            flash(f"删除角色失败：{exc}", "error")
            return redirect(url_for("people_settings"))
        flash("角色已删除。", "success")
        return redirect(url_for("people_settings"))

    @app.post("/projects/new")
    def create_project_from_ui() -> Any:
        title = request.form.get("title", "").strip()
        slug = request.form.get("slug", "").strip() or None
        question = request.form.get("question", "").strip()
        objective = request.form.get("objective", "").strip()
        if not title:
            flash("请先填写项目标题。", "error")
            return redirect(url_for("index"))
        try:
            project_dir = create_project(
                workspace_root,
                title=title,
                slug=slug,
                question=question,
                objective=objective,
            )
        except Exception as exc:  # noqa: BLE001
            flash(f"创建项目失败：{exc}", "error")
            return redirect(url_for("index"))
        flash(f"项目“{title}”已创建。", "success")
        return redirect(url_for("project_dashboard", slug=project_dir.name))

    @app.post("/settings/llm")
    def save_llm_settings() -> Any:
        mode = request.form.get("mode", "prompt-only").strip() or "prompt-only"
        base_url = request.form.get("base_url", "").strip() or "https://api.openai.com/v1"
        model = request.form.get("model", "").strip() or "gpt-5"
        api_key_env = request.form.get("api_key_env", "").strip() or "OPENAI_API_KEY"
        api_key = request.form.get("api_key", "").strip()
        _update_llm_config(
            workspace_root,
            {
                "mode": mode,
                "base_url": base_url,
                "model": model,
                "api_key_env": api_key_env,
            },
        )
        if api_key:
            _save_secrets(workspace_root, api_key_env, api_key)
            flash("接入设置已保存，密钥也已经更新。", "success")
        else:
            flash("接入设置已保存，本次没有修改密钥。", "success")
        next_url = request.form.get("next") or url_for("api_settings")
        return redirect(next_url)

    @app.get("/projects/<slug>")
    def project_dashboard(slug: str) -> str:
        try:
            project_dir = _project_dir(workspace_root, slug)
        except FileNotFoundError:
            abort(404)
        state = _load_ui_state(project_dir)
        grouped_cards = _load_project_cards(project_dir, state["active_roles"])
        econ_os_agents = grouped_cards.get("econ-os", [])
        econ_os_phases = [
            {
                "label": RESEARCH_STAGES[i]["label"],
                "cards": econ_os_agents[i * 2 : (i + 1) * 2],
            }
            for i in range(min(5, len(RESEARCH_STAGES)))
            if econ_os_agents[i * 2 : (i + 1) * 2]
        ]
        return render_template(
            "project.html",
            slug=slug,
            title=_project_title(project_dir),
            brief_text=_read_text(project_dir / "brief.md"),
            grouped_cards=grouped_cards,
            econ_os_phases=econ_os_phases,
            tickets=_load_tickets(project_dir),
            runs=_load_runs(project_dir),
            state=state,
            metrics=_project_metrics(project_dir),
            process_view=_project_process_view(workspace_root, state),
        )

    @app.post("/projects/<slug>/state")
    def update_project_state(slug: str) -> Any:
        try:
            project_dir = _project_dir(workspace_root, slug)
        except FileNotFoundError:
            abort(404)
        state = _load_ui_state(project_dir)
        role_specs = load_role_specs(workspace_root)
        active_roles = [role_id for role_id in request.form.getlist("active_roles") if role_id in role_specs]
        if not active_roles:
            active_roles = state["active_roles"]
        stage = request.form.get("stage", DEFAULT_STAGE).strip()
        if stage not in STAGE_OPTIONS:
            stage = DEFAULT_STAGE
        state["active_roles"] = active_roles
        state["stage"] = stage
        _save_ui_state(project_dir, state)
        flash("项目阶段和参与成员已更新。", "success")
        return redirect(url_for("project_dashboard", slug=slug))

    @app.post("/projects/<slug>/process")
    def update_project_process(slug: str) -> Any:
        try:
            project_dir = _project_dir(workspace_root, slug)
        except FileNotFoundError:
            abort(404)
        state = _load_ui_state(project_dir)
        process_templates = load_process_templates(workspace_root)
        role_specs = load_role_specs(workspace_root)
        process_id = request.form.get("process_id", "").strip() or state["process_id"]
        if process_id not in process_templates:
            flash("没有找到这套流程。", "error")
            return redirect(url_for("project_dashboard", slug=slug))
        selected_process = process_templates[process_id]
        step_ids = [str(step.get("id", "")).strip() for step in selected_process.get("steps", []) if str(step.get("id", "")).strip()]
        process_step = request.form.get("process_step", "").strip() or (step_ids[0] if step_ids else "")
        if process_step not in step_ids:
            process_step = step_ids[0] if step_ids else ""
        assignments: dict[str, list[str]] = {}
        for step in selected_process.get("steps", []):
            field_name = f"process_assignments_{step['id']}"
            assignments[step["id"]] = [role_id for role_id in request.form.getlist(field_name) if role_id in role_specs]
        state["process_id"] = process_id
        state["process_step"] = process_step
        state["process_assignments"] = assignments
        _save_ui_state(project_dir, state)
        flash("流程与成员安排已更新。", "success")
        return redirect(url_for("project_dashboard", slug=slug))

    @app.post("/projects/<slug>/decision")
    def add_pi_decision(slug: str) -> Any:
        try:
            project_dir = _project_dir(workspace_root, slug)
        except FileNotFoundError:
            abort(404)
        state = _load_ui_state(project_dir)
        decision = request.form.get("decision", "").strip()
        note = request.form.get("note", "").strip()
        if decision not in DECISION_OPTIONS:
            flash("这项 PI 决策暂时无法识别。", "error")
            return redirect(url_for("project_dashboard", slug=slug))
        state["pi_decisions"].insert(
            0,
            {
                "timestamp": dt.datetime.now().isoformat(timespec="seconds"),
                "decision": decision,
                "note": note,
            },
        )
        _save_ui_state(project_dir, state)
        flash("PI 决策已记录。", "success")
        return redirect(url_for("project_dashboard", slug=slug))

    @app.post("/projects/<slug>/run-role")
    def trigger_role(slug: str) -> Any:
        role_specs = load_role_specs(workspace_root)
        role_id = request.form.get("role_id", "").strip()
        if role_id not in role_specs:
            flash("没有找到这位成员。", "error")
            return redirect(url_for("project_dashboard", slug=slug))
        task = request.form.get("task", "").strip()
        extra_context = [line.strip() for line in request.form.get("context", "").splitlines() if line.strip()]
        execute = request.form.get("execute") == "on"
        try:
            result = run_role(
                workspace_root,
                project_slug=slug,
                role_id=role_id,
                task=task,
                extra_context=extra_context,
                execute=execute,
            )
        except Exception as exc:  # noqa: BLE001
            flash(f"{role_specs[role_id].name} 运行失败：{exc}", "error")
            return redirect(url_for("project_dashboard", slug=slug))
        mode_text = "已完成本轮产出" if execute else "已准备本轮说明"
        flash(f"{role_specs[role_id].name} {mode_text}。", "success")
        return redirect(url_for("project_dashboard", slug=slug))

    @app.post("/projects/<slug>/run-pipeline")
    def trigger_pipeline(slug: str) -> Any:
        preset = request.form.get("preset", "committee-review").strip()
        goal = request.form.get("goal", "").strip()
        execute = request.form.get("execute") == "on"
        try:
            results = run_pipeline(workspace_root, slug, preset, goal=goal, execute=execute)
        except Exception as exc:  # noqa: BLE001
            flash(f"整轮推进失败：{exc}", "error")
            return redirect(url_for("project_dashboard", slug=slug))
        preset_name = PIPELINE_LABELS.get(preset, preset)
        flash(f"{preset_name} 已完成，本轮共推进 {len(results)} 位成员。", "success")
        return redirect(url_for("project_dashboard", slug=slug))

    @app.post("/projects/<slug>/run-process")
    def trigger_process(slug: str) -> Any:
        try:
            project_dir = _project_dir(workspace_root, slug)
        except FileNotFoundError:
            abort(404)
        state = _load_ui_state(project_dir)
        process_view = _project_process_view(workspace_root, state)
        current_step = process_view.get("current_step")
        if not current_step:
            flash("当前流程还没有步骤。", "error")
            return redirect(url_for("project_dashboard", slug=slug))
        assigned_role_ids = current_step.get("assigned_role_ids", [])
        if not assigned_role_ids:
            flash("本流程尚未配置学生。", "error")
            return redirect(url_for("project_dashboard", slug=slug))
        extra_goal = request.form.get("goal", "").strip()
        execute = request.form.get("execute") == "on"
        role_specs = load_role_specs(workspace_root)
        for role_id in assigned_role_ids:
            task_parts = [
                f"当前流程：{process_view['selected']['name']}",
                f"当前步骤：{current_step['label']}",
                role_specs[role_id].default_task,
            ]
            if current_step.get("summary"):
                task_parts.append(f"步骤说明：{current_step['summary']}")
            if extra_goal:
                task_parts.append(f"PI 补充要求：{extra_goal}")
            try:
                run_role(
                    workspace_root,
                    project_slug=slug,
                    role_id=role_id,
                    task="\n\n".join(task_parts),
                    execute=execute,
                )
            except Exception as exc:  # noqa: BLE001
                flash(f"{role_specs[role_id].name} 运行失败：{exc}", "error")
                return redirect(url_for("project_dashboard", slug=slug))
        mode_text = "已完成本轮产出" if execute else "已准备本轮说明"
        flash(f"{process_view['selected']['name']} · {current_step['label']} {mode_text}。", "success")
        return redirect(url_for("project_dashboard", slug=slug))

    @app.post("/projects/<slug>/tickets")
    def create_project_ticket(slug: str) -> Any:
        role_specs = load_role_specs(workspace_root)
        role_id = request.form.get("role_id", "").strip()
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        inputs = request.form.get("inputs", "").strip()
        acceptance = request.form.get("acceptance", "").strip()
        assigned_by = request.form.get("assigned_by", "PI").strip() or "PI"
        if role_id not in role_specs or not title or not description:
            flash("创建任务单至少需要分配对象、标题和背景。", "error")
            return redirect(url_for("project_dashboard", slug=slug))
        try:
            ticket_path = create_ticket(
                workspace_root,
                project_slug=slug,
                role_id=role_id,
                title=title,
                description=description,
                assigned_by=assigned_by,
                inputs=inputs,
                acceptance=acceptance,
            )
        except Exception as exc:  # noqa: BLE001
            flash(f"任务单创建失败：{exc}", "error")
            return redirect(url_for("project_dashboard", slug=slug))
        flash("任务单已创建。", "success")
        return redirect(url_for("project_dashboard", slug=slug))

    @app.post("/projects/<slug>/delete")
    def delete_project_from_ui(slug: str) -> Any:
        try:
            delete_project(workspace_root, slug)
        except Exception as exc:  # noqa: BLE001
            flash(f"删除项目失败：{exc}", "error")
            return redirect(url_for("research_overview"))
        flash("项目已删除。", "success")
        return redirect(url_for("research_overview"))

    @app.get("/projects/<slug>/view")
    def view_project_file(slug: str) -> str:
        relative_path = request.args.get("path", "").strip()
        if not relative_path:
            abort(400)
        try:
            project_dir = _project_dir(workspace_root, slug)
            target = _resolve_project_path(project_dir, relative_path)
        except (FileNotFoundError, ValueError):
            abort(404)
        if not target.exists():
            abort(404)
        return render_template(
            "file_view.html",
            slug=slug,
            relative_path=relative_path,
            content=_read_text(target),
            file_path=target,
        )

    @app.post("/api/save-file/<path:file_path>")
    def save_file_api(file_path: str) -> Any:
        """保存文件内容的 API 端点"""
        content = request.form.get("content", "")
        try:
            target = workspace_root.joinpath(file_path).resolve()
            workspace_root_resolved = workspace_root.resolve()
            if target != workspace_root_resolved and workspace_root_resolved not in target.parents:
                return {"error": "路径安全检查失败"}, 403
            if not target.exists():
                return {"error": "文件不存在"}, 404
            target.write_text(content, encoding="utf-8")
            return {"success": True, "message": "文件已保存"}
        except Exception as exc:  # noqa: BLE001
            return {"error": str(exc)}, 500

    @app.get("/api/project/<slug>/context")
    def get_project_context_api(slug: str) -> Any:
        """获取项目的最新上下文（用于自动刷新）"""
        try:
            project_dir = _project_dir(workspace_root, slug)
            state = _load_ui_state(project_dir)
            runs = _load_runs(project_dir, limit=5)
            
            # 为每个 run 添加 slug，便于前端生成链接
            for run in runs:
                run['slug'] = slug
            
            return {
                "slug": slug,
                "metrics": _project_metrics(project_dir),
                "runs": runs,
                "tickets": _load_tickets(project_dir),
                "process_step": state.get("process_step"),
                "active_roles": len(state.get("active_roles", [])),
            }
        except FileNotFoundError:
            abort(404)

    return app


def launch_webui(root: Path | None = None, host: str = "127.0.0.1", port: int = 5010, debug: bool = False) -> None:
    workspace_root = find_workspace(root)
    ensure_workspace(workspace_root)
    app = create_app(workspace_root)
    app.run(host=host, port=port, debug=debug, use_reloader=False)
