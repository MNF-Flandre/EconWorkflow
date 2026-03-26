# Project Template Guide (.econ-os-template)

本文件用于说明如何基于 `.econ-os-template` 初始化单个项目，并保持与 Econ-OS 2.0 协议一致。

## Purpose

为每个课题提供统一的阶段目录、最小必需文件与回滚记录位置。

## Required Files (Per Project)

- `phase_1/` 到 `phase_5/` 阶段目录
- `decision_log.jsonl`（项目级审计日志）
- `project_config.yaml`（项目基础配置）
- 各阶段关键输出（见下表）

## Expected Outputs by Phase

| Phase | Purpose | Required files | Expected outputs | Validation | Rollback trigger |
|---|---|---|---|---|---|
| 1 | Discovery | `brief.md`, `context/research_question.md` | `lit_map.yaml`, `b2_audit_report.md`, `hypotheses.yaml` | gap / 假设可验证 | 重复研究或缺口不成立 |
| 2 | Design Lock | `hypotheses.yaml` | `design_lock.yaml`, `c2_data_availability_report.md` | 可得性审计通过 | 可得性不足或口径冲突 |
| 3 | Data Ops | `design_lock.yaml` | `clean_data.parquet`, `data_audit_scorecard.json` | 覆盖率与样本损失达标 | 质量不达标 |
| 4 | Econometrics | `design_lock.yaml`, `clean_data.parquet` | `baseline_regression.csv`, `regression_scorecard.json` | 稳健性通过率达标 | 稳健性不足 |
| 5 | Synthesis | `hypotheses.yaml`, `regression_scorecard.json` | `final_report.md`, `f2_peer_review_report.md` | 解释与证据一致 | 关键审稿意见未闭环 |

## Initialization Steps

1. 创建项目（推荐）：
   ```bash
   python -m econflow new-project "<title>" --slug <slug>
   ```
2. 确认项目目录中已存在各阶段结构。  
3. 按阶段运行 `pipeline` 或按角色执行 `delegate` / `run`。  
4. 在 `decision_log.jsonl` 持续记录关键决策与回滚。  

## Guardrails

- 不要绕过 `design_lock.yaml` 直接改执行口径。  
- 不要跳过审计输出直接推进下一阶段。  
- 阶段命名与输出路径应保持与 `AGENT_ROLES.md` 一致。
