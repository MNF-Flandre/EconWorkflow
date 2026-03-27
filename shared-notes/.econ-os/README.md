# Econ-OS 2.0 Protocol Layer Overview

本文件用于说明 `shared-notes/.econ-os/` 目录中的协议层设计：阶段、schema、门控与回滚规则。

## Purpose

Econ-OS 2.0 将研究流程拆成固定 5 阶段，并用标准化文件在阶段间交接，目标是让流程可追踪、可复核、可回滚。

## Core Principles

1. **Schema-driven handoff**：关键交付通过 YAML / JSON / JSONL 表达。  
2. **Dual-role validation**：每阶段包含执行者与审计者。  
3. **Design lock before execution**：Phase 2 锁定规格，后续执行遵循锁定口径。  
4. **Scorecard-based gate**：门控依据输出指标与阈值，不依赖主观口头判断。  

## 5-Phase Workflow

### Phase 1 — Discovery
- **Purpose:** 将研究想法转成可检验假设并完成文献去重审查。
- **Required files:** `phase_1/brief.md`, `context/research_question.md`
- **Expected outputs:** `phase_1/lit_map.yaml`, `phase_1/b2_audit_report.md`, `phase_1/hypotheses.yaml`
- **Validation:** `gap_defined == true` 且假设候选完整
- **Rollback trigger:** 审计确认重复研究或缺口不成立

### Phase 2 — Design Lock
- **Purpose:** 锁定变量定义、样本边界、固定效应与聚类口径。
- **Required files:** `phase_1/hypotheses.yaml`
- **Expected outputs:** `phase_2/design_lock.yaml`, `phase_2/c2_data_availability_report.md`
- **Validation:** 数据可得性满足阈值并完成审计
- **Rollback trigger:** 数据可得性不足或关键变量口径不一致

### Phase 3 — Data Ops
- **Purpose:** 产出可用于估计的数据集并完成质量审计。
- **Required files:** `phase_2/design_lock.yaml`
- **Expected outputs:** `phase_3/clean_data.parquet`, `phase_3/data_audit_scorecard.json`
- **Validation:** merge coverage、样本损失、主键与缺失值检查通过
- **Rollback trigger:** 样本损失或覆盖率低于设定阈值

### Phase 4 — Econometrics
- **Purpose:** 执行基准回归并完成稳健性压力测试。
- **Required files:** `phase_2/design_lock.yaml`, `phase_3/clean_data.parquet`
- **Expected outputs:** `phase_4/baseline_regression.csv`, `phase_4/regression_scorecard.json`
- **Validation:** 稳健性通过率达到阈值
- **Rollback trigger:** 稳健性不足，需退回设计层重审识别策略

### Phase 5 — Synthesis
- **Purpose:** 输出经济解释与审稿式复核结果。
- **Required files:** `phase_1/hypotheses.yaml`, `phase_4/regression_scorecard.json`
- **Expected outputs:** `phase_5/final_report.md`, `phase_5/f2_peer_review_report.md`
- **Validation:** 结论与证据链一致，审稿意见闭环
- **Rollback trigger:** 关键解释与证据不一致或审稿意见要求重大修订

## Protocol Files in This Directory

- `process_templates.json`: 流程步骤模板（Web UI / CLI 可读取）
- `schemas/`: hypotheses / design lock / scorecard / decision log / rollback schema
- `AGENT_ROLES.md`: 角色责任与输入输出契约
- `INTEGRATION_GUIDE.md`: 新项目接入与迁移说明
- `DEPLOYMENT_SUMMARY.md`: 当前公开仓库交付边界说明

## Runtime Notes (Public Defaults)

- 默认模式为 `prompt-only`，可在无 API key 情况下体验工作流。  
- 仅当 `[llm].mode = "openai-compatible"` 且命令带 `--execute` 时，系统才会请求模型。
