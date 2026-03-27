# Econ-OS 2.0 Agent Role Mapping

本文件用于快速查看 Econ-OS 2.0 在本仓库中的角色集合与阶段映射。

## Phase-to-Role Mapping

| Phase | Role ID | Role Name | Primary Deliverable |
|---|---|---|---|
| Phase 1 | `b1_explorer` | Literature Explorer | `phase_1/lit_map.yaml` |
| Phase 1 | `b2_challenger` | Literature Challenger | `phase_1/b2_audit_report.md` |
| Phase 2 | `c1_designer` | Specification Designer | `phase_2/design_lock.yaml` |
| Phase 2 | `c2_data_auditor` | Data Availability Auditor | `phase_2/c2_data_availability_report.md` |
| Phase 3 | `d1_engineer` | Data Engineer | `phase_3/clean_data.parquet` |
| Phase 3 | `d2_qa_auditor` | Data QA Auditor | `phase_3/data_audit_scorecard.json` |
| Phase 4 | `e1_runner` | Econometrics Runner | `phase_4/baseline_regression.csv` |
| Phase 4 | `e2_adversarial_auditor` | Adversarial Auditor | `phase_4/regression_scorecard.json` |
| Phase 5 | `f1_narrator` | Economics Narrator | `phase_5/final_report.md` |
| Phase 5 | `f2_journal_reviewer` | Journal Reviewer | `phase_5/f2_peer_review_report.md` |

## Usage Notes

- 默认通过 `pipeline --preset econ-os-2.0` 触发完整流程。
- 也可通过 `delegate` 为单角色发任务票据。
- 默认运行模式是 `prompt-only`，便于无 API key 的本地演示。
- 角色契约、输入输出与 guardrails 以 `shared-notes/.econ-os/AGENT_ROLES.md` 为准。
