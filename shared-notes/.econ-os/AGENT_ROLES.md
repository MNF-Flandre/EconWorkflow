# Econ-OS 2.0 Agent Roles

本文件用于定义 Econ-OS 2.0 角色契约，供维护者分配任务与校验交付物时引用。

## Role Catalog

| Phase | Role ID | Role | Responsibility | Primary Output |
|---|---|---|---|---|
| 1 | `b1_explorer` | Literature Explorer | 文献检索与缺口提炼 | `phase_1/lit_map.yaml` |
| 1 | `b2_challenger` | Literature Challenger | 独立挑战与重复研究审查 | `phase_1/b2_audit_report.md` |
| 2 | `c1_designer` | Specification Designer | 变量、样本、识别规格设计 | `phase_2/design_lock.yaml` |
| 2 | `c2_data_auditor` | Data Availability Auditor | 数据可得性与口径审计 | `phase_2/c2_data_availability_report.md` |
| 3 | `d1_engineer` | Data Engineer | 数据清洗与结构化产出 | `phase_3/clean_data.parquet` |
| 3 | `d2_qa_auditor` | Data QA Auditor | 数据质量审计与分数卡 | `phase_3/data_audit_scorecard.json` |
| 4 | `e1_runner` | Econometrics Runner | 基准估计执行 | `phase_4/baseline_regression.csv` |
| 4 | `e2_adversarial_auditor` | Adversarial Auditor | 稳健性压力测试 | `phase_4/regression_scorecard.json` |
| 5 | `f1_narrator` | Economics Narrator | 经济解释与叙述组织 | `phase_5/final_report.md` |
| 5 | `f2_journal_reviewer` | Journal Reviewer | 同行评审式质检 | `phase_5/f2_peer_review_report.md` |

## Standard Role Contract Template

每个角色都遵循同一结构：

- **Role**: 角色名称与 ID
- **Responsibility**: 该角色负责完成的核心目标
- **Inputs**: 运行时必须读取的阶段输入文件
- **Outputs**: 该角色必须产出的文件
- **Guardrails**: 禁止越界修改、必须记录决策、必须对齐 design lock 等约束

## Role Contracts (Condensed)

### Role: `b1_explorer`
- **Responsibility:** 形成可复核的文献地图与候选假设基础。
- **Inputs:** `phase_1/brief.md`, `context/research_question.md`
- **Outputs:** `phase_1/lit_map.yaml`
- **Guardrails:** 不直接下最终结论；需为审计角色保留可追踪证据。

### Role: `b2_challenger`
- **Responsibility:** 对 B1 结果进行独立反证与重复性审查。
- **Inputs:** `phase_1/lit_map.yaml`
- **Outputs:** `phase_1/b2_audit_report.md`
- **Guardrails:** 关注可证伪点与冲突证据；明确是否触发回退建议。

### Role: `c1_designer`
- **Responsibility:** 将假设映射为可执行规格并形成锁定草案。
- **Inputs:** `phase_1/hypotheses.yaml`
- **Outputs:** `phase_2/design_lock.yaml`
- **Guardrails:** 规格表达需可审计、可复算，不得留空关键定义。

### Role: `c2_data_auditor`
- **Responsibility:** 审计规格中的数据可得性与口径一致性。
- **Inputs:** `phase_2/design_lock.yaml`
- **Outputs:** `phase_2/c2_data_availability_report.md`
- **Guardrails:** 不得跳过关键变量核验；需量化可得性判断。

### Role: `d1_engineer`
- **Responsibility:** 按锁定规格执行数据工程。
- **Inputs:** `phase_2/design_lock.yaml`
- **Outputs:** `phase_3/clean_data.parquet`
- **Guardrails:** 不得擅自改规格；所有关键处理应可追踪。

### Role: `d2_qa_auditor`
- **Responsibility:** 对数据产出做质量评分与门控建议。
- **Inputs:** `phase_2/design_lock.yaml`, `phase_3/d1_cleaning_log.md`
- **Outputs:** `phase_3/data_audit_scorecard.json`
- **Guardrails:** 明确通过/警告/回退条件，不仅给定性意见。

### Role: `e1_runner`
- **Responsibility:** 执行基准估计并导出主结果。
- **Inputs:** `phase_2/design_lock.yaml`, `phase_3/clean_data.parquet`
- **Outputs:** `phase_4/baseline_regression.csv`
- **Guardrails:** 不得偏离锁定识别口径；结果文件需结构化。

### Role: `e2_adversarial_auditor`
- **Responsibility:** 进行稳健性与对抗性检验。
- **Inputs:** `phase_2/design_lock.yaml`, `phase_4/baseline_regression.csv`
- **Outputs:** `phase_4/regression_scorecard.json`
- **Guardrails:** 需覆盖约定压力测试；明确稳健性通过率。

### Role: `f1_narrator`
- **Responsibility:** 形成结果解释与叙述主线。
- **Inputs:** `phase_1/hypotheses.yaml`, `phase_4/regression_scorecard.json`
- **Outputs:** `phase_5/final_report.md`
- **Guardrails:** 解释必须绑定证据，不夸大外推。

### Role: `f2_journal_reviewer`
- **Responsibility:** 以审稿视角识别方法与解释风险。
- **Inputs:** `phase_5/final_report.md`, `phase_4/regression_scorecard.json`
- **Outputs:** `phase_5/f2_peer_review_report.md`
- **Guardrails:** 评论应可执行、可追踪，区分重大与次要问题。
