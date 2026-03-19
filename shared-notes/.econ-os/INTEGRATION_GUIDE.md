# Econ-OS 2.0 集成简表

- 研究流程：固定 5 阶段（Phase 1–5），默认模板位于 `shared-notes/process_templates.json`。
- 角色集合：仅包含 Econ-OS 2.0 十个角色（b1–f2），不再支持博士生/硕士生旧分层。
- 关键交付：
  - Phase 1: `lit_map.yaml`、`b2_audit_report.md`
  - Phase 2: `design_lock.yaml`、`c2_data_availability_report.md`
  - Phase 3: `clean_data.parquet`、`data_audit_scorecard.json`
  - Phase 4: `baseline_regression.csv`、`regression_scorecard.json`
  - Phase 5: `final_report.md`、`f2_peer_review_report.md`
- 审计日志：全流程决策与回滚记录在 `decision_log.jsonl`。
- 集成建议：保持文件命名一致；在 WebUI “流程推进”中为每个步骤至少配置一名 Econ-OS 角色后再运行。
