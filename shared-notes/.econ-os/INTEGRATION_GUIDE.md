# Econ-OS 2.0 Integration Guide

本文件用于指导维护者把 Econ-OS 2.0 协议层接入到本仓库或迁移到已有项目。

## Purpose

保证新项目与存量项目都能对齐同一套阶段结构、角色契约与 schema 交接规则。

## Required Files

- `shared-notes/.econ-os/process_templates.json`
- `shared-notes/.econ-os/AGENT_ROLES.md`
- `shared-notes/.econ-os/schemas/*`
- `workflow.toml`（指向上述模板与角色文件）
- `projects/.econ-os-template/`（项目初始化模板）

## New Project Integration (Recommended)

1. 确认仓库根目录存在 `workflow.toml` 且 `active_workflow = "econ-os-2.0"`。  
2. 使用 `python -m econflow new-project ...` 创建项目。  
3. 在项目目录中确认阶段目录与模板文件已生成。  
4. 用 `python -m econflow status --project <slug>` 检查状态。  
5. 先运行 `pipeline`（不加 `--execute`）验证 prompt-only 路径。  

## Existing Project Migration (Incremental)

1. 先对齐目录：确保有 `phase_1` 到 `phase_5`。  
2. 把历史产物映射到对应阶段输出命名。  
3. 用 schema 校验关键文件字段完整度。  
4. 从当前阶段继续推进，不要求重跑已完成阶段。  

## Validation Checklist

- [ ] `workflow.toml` 与 README 对默认模式描述一致（默认 `prompt-only`）
- [ ] 角色输出路径与 `AGENT_ROLES.md` 一致
- [ ] `decision_log.jsonl` 可持续追加并可读
- [ ] 回滚触发条件在文档中有明确说明
- [ ] CLI `status / pipeline / delegate` 能在本地给出可理解输出

## Rollback Trigger (Integration-level)

当以下情况出现时，优先回到上一可验证节点修订：
- 输出文件命名与 schema 约定持续不一致
- 阶段关键文件缺失，导致后续角色无法接力
- 文档、配置、CLI 行为对默认模式描述冲突
