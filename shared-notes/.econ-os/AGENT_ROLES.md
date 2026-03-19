# Econ-OS 2.0 研究角色一览

Econ-OS 2.0 只包含 10 个平铺的研究角色，每个阶段都有执行者与对抗性审计员：

| 阶段 | 角色ID | 名称 | 主要交付 |
| --- | --- | --- | --- |
| Phase 1 | b1_explorer | 文献探索者 | `phase_1/lit_map.yaml` |
| Phase 1 | b2_challenger | 文献挑战者 | `phase_1/b2_audit_report.md` |
| Phase 2 | c1_designer | 规格设计师 | `phase_2/design_lock.yaml` |
| Phase 2 | c2_data_auditor | 数据可得性审计员 | `phase_2/c2_data_availability_report.md` |
| Phase 3 | d1_engineer | 数据工程师 | `phase_3/clean_data.parquet` |
| Phase 3 | d2_qa_auditor | 数据质控审计员 | `phase_3/data_audit_scorecard.json` |
| Phase 4 | e1_runner | 回归执行者 | `phase_4/baseline_regression.csv` |
| Phase 4 | e2_adversarial_auditor | 稳健性审计员 | `phase_4/regression_scorecard.json` |
| Phase 5 | f1_narrator | 经济解释者 | `phase_5/final_report.md` |
| Phase 5 | f2_journal_reviewer | 期刊审稿人 | `phase_5/f2_peer_review_report.md` |

所有角色均在 `agents/` 下提供默认角色卡，可按需编辑；不再维护任何博士生/硕士生的旧角色映射。
