from __future__ import annotations

import datetime as dt
import json
import re
import shutil
import textwrap
import tomllib
from dataclasses import dataclass
from pathlib import Path

from econflow.llm import LLMConfig, generate_response

DEFAULT_CONFIG = textwrap.dedent(
    """\
    [workspace]
    name = "econ-research-workflow"
    default_language = "zh-CN"
    projects_dir = "projects"
    agents_dir = "agents"
    shared_notes_dir = "shared-notes"

    [llm]
    # 默认不调模型。若要调用模型，请将 mode 设置为 "openai-compatible"，并配置对应的 API 密钥。
    mode = "prompt-only"
    base_url = "https://api.openai.com/v1"
    model = "gpt-4"
    api_key_env = "OPENAI_API_KEY"
    temperature = 0.2
    max_tokens = 4000
"""
)


@dataclass(frozen=True)
class WorkspaceConfig:
    root: Path
    projects_dir: Path
    agents_dir: Path
    shared_notes_dir: Path
    llm: LLMConfig


@dataclass(frozen=True)
class RoleSpec:
    name: str
    layer: str
    deliverable: str
    default_task: str
    context_files: tuple[str, ...]


@dataclass(frozen=True)
class RunResult:
    role_id: str
    project_slug: str
    run_dir: Path
    prompt_path: Path
    metadata_path: Path
    response_path: Path | None
    deliverable_path: Path
    executed: bool


CUSTOM_ROLE_SPECS_FILE = "_custom_roles.json"


DEFAULT_ROLE_SPECS: dict[str, RoleSpec] = {
    "b1_explorer": RoleSpec(
        name="文献探索者",
        layer="econ-os",
        deliverable="phase_1/lit_map.yaml",
        default_task="系统检索相关文献，综合整理文献矩阵，提炼研究缺口与假设方向",
        context_files=("phase_1/brief.md", "context/research_question.md"),
    ),
    "b2_challenger": RoleSpec(
        name="文献挑战者",
        layer="econ-os",
        deliverable="phase_1/b2_audit_report.md",
        default_task="独立审查文献探索者的结论，寻找冲突证据和已发表的重复研究，出具挑战报告",
        context_files=("phase_1/lit_map.yaml",),
    ),
    "c1_designer": RoleSpec(
        name="规格设计师",
        layer="econ-os",
        deliverable="phase_2/design_lock.yaml",
        default_task="将研究假设映射为具体变量定义、样本边界、固定效应和聚类口径，锁定实证规格",
        context_files=("phase_1/hypotheses.yaml",),
    ),
    "c2_data_auditor": RoleSpec(
        name="数据可得性审计员",
        layer="econ-os",
        deliverable="phase_2/c2_data_availability_report.md",
        default_task="逐一核查规格中每个变量的数据来源、可得性与口径一致性，评估数据匹配的可行性",
        context_files=("phase_2/design_lock.yaml",),
    ),
    "d1_engineer": RoleSpec(
        name="数据工程师",
        layer="econ-os",
        deliverable="phase_3/clean_data.parquet",
        default_task="按照锁定的实证规格执行数据清洗、样本合并、变量滞后与缩尾处理，产出分析用数据集",
        context_files=("phase_2/design_lock.yaml",),
    ),
    "d2_qa_auditor": RoleSpec(
        name="数据质控审计员",
        layer="econ-os",
        deliverable="phase_3/data_audit_scorecard.json",
        default_task="审计样本流失路径、主键唯一性与缺失值分布，判断数据质量是否达标，决定是否继续推进或回退重做",
        context_files=("phase_2/design_lock.yaml", "phase_3/d1_cleaning_log.md"),
    ),
    "e1_runner": RoleSpec(
        name="回归执行者",
        layer="econ-os",
        deliverable="phase_4/baseline_regression.csv",
        default_task="按照锁定规格执行基准回归，应用指定的固定效应与聚类口径，产出核心估计结果",
        context_files=("phase_2/design_lock.yaml", "phase_3/clean_data.parquet"),
    ),
    "e2_adversarial_auditor": RoleSpec(
        name="稳健性审计员",
        layer="econ-os",
        deliverable="phase_4/regression_scorecard.json",
        default_task="对基准结果启动全套稳健性压力测试，包括更换聚类层级、安慰剂检验、排除极端值和子样本分析，评判结果是否稳健",
        context_files=("phase_2/design_lock.yaml", "phase_4/baseline_regression.csv"),
    ),
    "f1_narrator": RoleSpec(
        name="经济解释者",
        layer="econ-os",
        deliverable="phase_5/final_report.md",
        default_task="对比假设与回归结果，解释系数的经济含义，撰写最终报告草稿",
        context_files=("phase_1/hypotheses.yaml", "phase_4/regression_scorecard.json"),
    ),
    "f2_journal_reviewer": RoleSpec(
        name="期刊审稿人",
        layer="econ-os",
        deliverable="phase_5/f2_peer_review_report.md",
        default_task="模拟顶级期刊审稿人进行严格评审，重点检查内生性处理、过度解释风险和研究设计缺陷，出具学术质量评估意见",
        context_files=("phase_5/final_report.md",),
    ),
}

# Backward-compatible alias for callers that still import ROLE_SPECS directly.
ROLE_SPECS = DEFAULT_ROLE_SPECS

PIPELINES: dict[str, tuple[str, ...]] = {
    "econ-os-2.0": (
        "b1_explorer",
        "b2_challenger",
        "c1_designer",
        "c2_data_auditor",
        "d1_engineer",
        "d2_qa_auditor",
        "e1_runner",
        "e2_adversarial_auditor",
        "f1_narrator",
        "f2_journal_reviewer",
    ),
}


def find_workspace(start: Path | None = None) -> Path:
    current = (start or Path.cwd()).resolve()
    for candidate in [current, *current.parents]:
        if (candidate / "workflow.toml").exists() and (candidate / "agents").exists():
            return candidate
    fallback = Path(__file__).resolve().parent.parent
    if (fallback / "workflow.toml").exists():
        return fallback
    raise RuntimeError("没有找到工作流根目录。")


def is_builtin_role(role_id: str) -> bool:
    return role_id in DEFAULT_ROLE_SPECS


def _custom_role_specs_path(root: Path) -> Path:
    config = load_config(root)
    return config.agents_dir / CUSTOM_ROLE_SPECS_FILE


def _serialize_role_spec(spec: RoleSpec) -> dict[str, object]:
    return {
        "name": spec.name,
        "layer": spec.layer,
        "deliverable": spec.deliverable,
        "default_task": spec.default_task,
        "context_files": list(spec.context_files),
    }


def _deserialize_role_spec(payload: dict[str, object]) -> RoleSpec:
    return RoleSpec(
        name=str(payload.get("name", "")).strip(),
        layer=str(payload.get("layer", "econ-os")).strip() or "econ-os",
        deliverable=str(payload.get("deliverable", "")).strip(),
        default_task=str(payload.get("default_task", "")).strip(),
        context_files=tuple(str(item).strip() for item in payload.get("context_files", []) if str(item).strip()),
    )


def load_role_specs(root: Path | None = None) -> dict[str, RoleSpec]:
    workspace_root = find_workspace(root)
    merged = dict(DEFAULT_ROLE_SPECS)
    custom_path = _custom_role_specs_path(workspace_root)
    if not custom_path.exists():
        return merged
    try:
        payload = json.loads(custom_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return merged
    if not isinstance(payload, dict):
        return merged
    for role_id, raw_spec in payload.items():
        if not isinstance(raw_spec, dict):
            continue
        spec = _deserialize_role_spec(raw_spec)
        if not spec.name or spec.layer not in {"econ-os"} or not spec.deliverable or not spec.default_task:
            continue
        merged[str(role_id).strip()] = spec
    return merged


def save_custom_role(root: Path, role_id: str, spec: RoleSpec) -> None:
    workspace_root = find_workspace(root)
    if is_builtin_role(role_id):
        raise RuntimeError("默认角色不能写入自定义角色清单。")
    custom_path = _custom_role_specs_path(workspace_root)
    custom_path.parent.mkdir(parents=True, exist_ok=True)
    payload: dict[str, object] = {}
    if custom_path.exists():
        try:
            existing = json.loads(custom_path.read_text(encoding="utf-8"))
            if isinstance(existing, dict):
                payload = existing
        except json.JSONDecodeError:
            payload = {}
    payload[role_id] = _serialize_role_spec(spec)
    custom_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def delete_custom_role(root: Path, role_id: str) -> None:
    workspace_root = find_workspace(root)
    if is_builtin_role(role_id):
        raise RuntimeError("默认角色不能删除。")
    custom_path = _custom_role_specs_path(workspace_root)
    payload: dict[str, object] = {}
    if custom_path.exists():
        try:
            existing = json.loads(custom_path.read_text(encoding="utf-8"))
            if isinstance(existing, dict):
                payload = existing
        except json.JSONDecodeError:
            payload = {}
    payload.pop(role_id, None)
    if payload:
        custom_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    elif custom_path.exists():
        custom_path.unlink()


def ensure_workspace(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    if not (root / "workflow.toml").exists():
        (root / "workflow.toml").write_text(DEFAULT_CONFIG, encoding="utf-8")
    for name in ("projects", "shared-notes", "agents"):
        (root / name).mkdir(parents=True, exist_ok=True)
    for role_id in DEFAULT_ROLE_SPECS:
        role_dir = root / "agents" / role_id
        role_dir.mkdir(parents=True, exist_ok=True)
        role_path = role_dir / "role.md"
        memory_path = role_dir / "memory.md"
        if not role_path.exists():
            role_path.write_text(f"# {role_id}\n\n待补充角色卡。\n", encoding="utf-8")
        if not memory_path.exists():
            memory_path.write_text("# Memory\n\n- 待补充长期偏好。\n", encoding="utf-8")


def load_config(root: Path) -> WorkspaceConfig:
    with (root / "workflow.toml").open("rb") as handle:
        data = tomllib.load(handle)
    workspace = data.get("workspace") or {}
    llm = data.get("llm") or {}
    llm_config = LLMConfig(
        mode=str(llm.get("mode", "prompt-only")),
        base_url=str(llm.get("base_url", "https://api.openai.com/v1")),
        model=str(llm.get("model", "gpt-4")),
        api_key_env=str(llm.get("api_key_env", "OPENAI_API_KEY")),
        temperature=float(llm.get("temperature", 0.2)),
        max_tokens=int(llm.get("max_tokens", 4000)),
    )
    return WorkspaceConfig(
        root=root,
        projects_dir=root / str(workspace.get("projects_dir", "projects")),
        agents_dir=root / str(workspace.get("agents_dir", "agents")),
        shared_notes_dir=root / str(workspace.get("shared_notes_dir", "shared-notes")),
        llm=llm_config,
    )


def slugify(text: str) -> str:
    lowered = text.strip().lower()
    normalized = re.sub(r"[^\w\s-]", " ", lowered, flags=re.UNICODE)
    collapsed = re.sub(r"[\s_]+", "-", normalized, flags=re.UNICODE)
    return collapsed.strip("-") or dt.datetime.now().strftime("project-%Y%m%d-%H%M%S")


def create_project(root: Path, title: str, slug: str | None = None, question: str = "", objective: str = "") -> Path:
    ensure_workspace(root)
    config = load_config(root)
    project_slug = slugify(slug or title)
    project_dir = config.projects_dir / project_slug
    if project_dir.exists():
        raise RuntimeError(f"课题已存在: {project_slug}")

    files = {
        "brief.md": textwrap.dedent(
            f"""\
            # {title}

            {objective.strip() or question.strip() or '待补充项目简介'}
            """
        ),
        "context/research_question.md": f"# Research Question\n\n{question.strip() or '待补充'}\n",
        "context/constraints.md": "# Constraints\n\n- 时间约束：待补充\n- 数据约束：待补充\n- 方法约束：待补充\n",
        "literature/notes.md": "# Literature Notes\n\n- 待补充\n",
        "data/raw/README.md": "# Raw Data\n\n原始数据放这里。\n",
        "data/processed/README.md": "# Processed Data\n\n清洗后数据放这里。\n",
        "analysis/code/README.md": "# Code\n\nR / Python / Stata 脚本放这里。\n",
        "analysis/tables/README.md": "# Tables\n\n表格输出放这里。\n",
        "analysis/figures/README.md": "# Figures\n\n图形输出放这里。\n",
        "tickets/open/README.md": "# Open Tickets\n\nPI 发给研究角色的任务单放这里。\n",
        "tickets/done/README.md": "# Done Tickets\n\n完成的任务单移到这里。\n",
    }
    for role_id, spec in load_role_specs(root).items():
        files[spec.deliverable] = f"# {spec.name}\n\n待生成。\n"
    for relative_path, content in files.items():
        path = project_dir / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    (project_dir / "runs").mkdir(parents=True, exist_ok=True)
    return project_dir


def create_custom_role(
    root: Path,
    *,
    role_id: str,
    name: str,
    layer: str,
    default_task: str,
    context_files: tuple[str, ...] = ("brief.md",),
) -> RoleSpec:
    ensure_workspace(root)
    workspace_root = find_workspace(root)
    normalized_role_id = slugify(role_id)
    if not normalized_role_id:
        raise RuntimeError("角色标识不能为空。")
    role_specs = load_role_specs(workspace_root)
    if normalized_role_id in role_specs:
        raise RuntimeError(f"角色已存在: {normalized_role_id}")
    normalized_layer = layer.strip().lower()
    if normalized_layer not in {"econ-os"}:
        raise RuntimeError("角色层级必须是 econ-os。")
    deliverable_name = f"{normalized_role_id}.md"
    spec = RoleSpec(
        name=name.strip() or normalized_role_id,
        layer=normalized_layer,
        deliverable=f"outputs/{deliverable_name}",
        default_task=default_task.strip() or "请根据项目目标完成本轮研究任务。",
        context_files=tuple(item for item in context_files if item.strip()) or ("brief.md",),
    )
    save_custom_role(workspace_root, normalized_role_id, spec)
    config = load_config(workspace_root)
    role_dir = config.agents_dir / normalized_role_id
    role_dir.mkdir(parents=True, exist_ok=True)
    if not (role_dir / "role.md").exists():
        (role_dir / "role.md").write_text(
            f"# {spec.name}\n\n你是研究流程中的新成员，请按项目要求完成任务。\n",
            encoding="utf-8",
        )
    if not (role_dir / "memory.md").exists():
        (role_dir / "memory.md").write_text(f"# {spec.name} 记忆\n\n- 待补充稳定偏好。\n", encoding="utf-8")
    for project_dir in [path for path in config.projects_dir.iterdir() if path.is_dir()]:
        deliverable_path = project_dir / spec.deliverable
        deliverable_path.parent.mkdir(parents=True, exist_ok=True)
        if not deliverable_path.exists():
            deliverable_path.write_text(f"# {spec.name}\n\n待生成。\n", encoding="utf-8")
    return spec


def delete_role(root: Path, role_id: str) -> None:
    workspace_root = find_workspace(root)
    role_specs = load_role_specs(workspace_root)
    if role_id not in role_specs:
        raise RuntimeError(f"未找到角色: {role_id}")
    if is_builtin_role(role_id):
        raise RuntimeError("默认角色不能删除。")
    spec = role_specs[role_id]
    config = load_config(workspace_root)
    delete_custom_role(workspace_root, role_id)
    role_dir = config.agents_dir / role_id
    if role_dir.exists():
        shutil.rmtree(role_dir)
    for project_dir in [path for path in config.projects_dir.iterdir() if path.is_dir()]:
        deliverable_path = project_dir / spec.deliverable
        if deliverable_path.exists():
            deliverable_path.unlink()


def delete_project(root: Path, project_slug: str) -> None:
    config = load_config(find_workspace(root))
    project_dir = config.projects_dir / project_slug
    if not project_dir.exists():
        raise RuntimeError(f"未找到课题: {project_slug}")
    shutil.rmtree(project_dir)


def create_ticket(
    root: Path,
    project_slug: str,
    role_id: str,
    title: str,
    description: str,
    assigned_by: str = "PI",
    inputs: str = "",
    acceptance: str = "",
) -> Path:
    role_specs = load_role_specs(root)
    if role_id not in role_specs:
        raise RuntimeError(f"未知角色: {role_id}")
    project_dir = load_config(root).projects_dir / project_slug
    if not project_dir.exists():
        raise RuntimeError(f"未找到课题: {project_slug}")
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    ticket_path = project_dir / "tickets" / "open" / f"{stamp}_{role_id}_{slugify(title)}.md"
    content = textwrap.dedent(
        f"""\
        # {title}

        - Assigned by: {assigned_by}
        - Assigned to: {role_specs[role_id].name} ({role_id})
        - Status: OPEN
        - Created at: {dt.datetime.now().isoformat(timespec="seconds")}

        ## Background

        {description.strip() or '待补充'}

        ## Inputs

        {inputs.strip() or '待补充'}

        ## Deliverable

        {role_specs[role_id].deliverable}

        ## Acceptance

        {acceptance.strip() or '待补充'}
        """
    )
    ticket_path.write_text(content, encoding="utf-8")
    return ticket_path


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _next_run_dir(project_dir: Path, role_id: str) -> Path:
    while True:
        stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        candidate = project_dir / "runs" / f"{stamp}_{role_id}"
        if not candidate.exists():
            return candidate


def _prompt_for(project_dir: Path, role_id: str, task: str, extra_context: list[str]) -> tuple[str, list[str]]:
    spec = load_role_specs(project_dir.parent.parent)[role_id]
    role_text = _read(project_dir.parent.parent / "agents" / role_id / "role.md")
    memory_text = _read(project_dir.parent.parent / "agents" / role_id / "memory.md")
    context_paths = list(spec.context_files) + list(extra_context)
    blocks: list[str] = []
    used_paths: list[str] = []
    for relative_path in context_paths:
        file_path = project_dir / relative_path
        if file_path.exists():
            used_paths.append(relative_path)
            blocks.append(f"## File: {relative_path}\n\n{_read(file_path).strip() or '(empty)'}")
    prompt = textwrap.dedent(
        f"""\
        Date: {dt.datetime.now().isoformat(timespec="seconds")}
        Project: {project_dir.name}
        Role: {role_id}

        ## Role Card

        {role_text.strip()}

        ## Memory

        {memory_text.strip()}

        ## Task

        {task.strip()}

        ## Context

        {chr(10).join(blocks) if blocks else 'No context files found.'}

        ## Output Rules

        - Assume the user is the tenure-track PI.
        - Write in Chinese Markdown.
        - Start with verdicts and risks.
        - If evidence is insufficient, say so directly.
        """
    )
    return prompt, used_paths


def run_role(
    root: Path,
    project_slug: str,
    role_id: str,
    task: str = "",
    extra_context: list[str] | None = None,
    execute: bool = False,
) -> RunResult:
    role_specs = load_role_specs(root)
    if role_id not in role_specs:
        raise RuntimeError(f"未知角色: {role_id}")
    config = load_config(root)
    project_dir = config.projects_dir / project_slug
    if not project_dir.exists():
        raise RuntimeError(f"未找到课题: {project_slug}")
    spec = role_specs[role_id]
    run_dir = _next_run_dir(project_dir, role_id)
    run_dir.mkdir(parents=True, exist_ok=False)
    effective_task = task.strip() or spec.default_task
    prompt, used_paths = _prompt_for(project_dir, role_id, effective_task, extra_context or [])
    prompt_path = run_dir / "prompt.md"
    metadata_path = run_dir / "metadata.json"
    prompt_path.write_text(prompt, encoding="utf-8")
    metadata_path.write_text(
        json.dumps(
            {
                "project": project_slug,
                "role": role_id,
                "task": effective_task,
                "context": used_paths,
                "executed": execute,
                "deliverable": spec.deliverable,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    response_path = None
    deliverable_path = project_dir / spec.deliverable
    if execute:
        role_text = _read(config.agents_dir / role_id / "role.md")
        response = generate_response(config.llm, system_prompt=role_text.strip(), user_prompt=prompt)
        response_path = run_dir / "response.md"
        response_path.write_text(response, encoding="utf-8")
        deliverable_path.write_text(response, encoding="utf-8")
        with (config.agents_dir / role_id / "memory.md").open("a", encoding="utf-8") as handle:
            handle.write(
                f"\n\n## {dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | {project_slug}\n"
                f"- Task: {effective_task}\n"
            )
    return RunResult(role_id, project_slug, run_dir, prompt_path, metadata_path, response_path, deliverable_path, execute)


def run_pipeline(root: Path, project_slug: str, preset: str, goal: str = "", execute: bool = False) -> list[RunResult]:
    if preset not in PIPELINES:
        raise RuntimeError(f"未知预设: {preset}")
    results: list[RunResult] = []
    role_specs = load_role_specs(root)
    for role_id in PIPELINES[preset]:
        task = role_specs[role_id].default_task
        if goal.strip():
            task = f"{task}\n\nPI 额外要求：{goal.strip()}"
        results.append(run_role(root, project_slug, role_id, task=task, execute=execute))
    return results


def project_status(root: Path, project_slug: str | None = None) -> dict[str, object]:
    config = load_config(root)
    role_specs = load_role_specs(root)
    projects: list[dict[str, object]] = []
    for project_dir in sorted([p for p in config.projects_dir.iterdir() if p.is_dir()], key=lambda p: p.name):
        if project_slug and project_dir.name != project_slug:
            continue
        open_tickets = [
            path
            for path in (project_dir / "tickets" / "open").glob("*.md")
            if path.name.lower() != "readme.md"
        ]
        deliverables = {
            role_id: (project_dir / spec.deliverable).exists() and "待生成" not in _read(project_dir / spec.deliverable)
            for role_id, spec in role_specs.items()
        }
        runs = sorted([path.name for path in (project_dir / "runs").glob("*") if path.is_dir()])
        projects.append(
            {
                "slug": project_dir.name,
                "path": str(project_dir),
                "open_tickets": len(open_tickets),
                "latest_run": runs[-1] if runs else "",
                "deliverables": deliverables,
            }
        )
    return {"root": str(config.root), "projects": projects}
