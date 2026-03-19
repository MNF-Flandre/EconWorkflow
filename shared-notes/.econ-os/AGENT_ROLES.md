# Econ-OS 2.0 Agent Role Mapping
# How existing RA & PhD agents map to new phase-based framework

## Mapping Overview

| 旧角色 | 新角色编号 | 新角色名 | 从属Phase | 功能定位 |
|------|----------|---------|----------|--------|
| ma_literature | B1 + B2 | Literature Explorer + Challenger | Phase 1 | 文献查证与冲突检测 |
| ma_data | C2 | Data Availability Auditor | Phase 2 | 数据可得性审计 |
| ma_cleaning | D1 | Data Engineer | Phase 3 | 数据清洗与工程 |
| (NEW) data auditor | D2 | Data Quality Auditor | Phase 3 | 数据质量与sample loss检查 |
| ma_regression | E1 | Baseline Regression Runner | Phase 4 | 回归执行 |
| (NEW) adversarial auditor | E2 | Stress Test Auditor | Phase 4 | 鲁棒性与对抗性测试 |
| phd_story | F1 | Economics Narrator | Phase 5 | 经济解释与叙事 |
| phd_feasibility | Combined | Multiple (phase router) | All | 项目可行性评估（前置） |
| ma_replication | External | Replication Verifier | Post-Phase 5 | 独立复现验证 |

---

## Detailed Agent Specifications (Econ-OS 2.0)

### PHASE 1: DISCOVERY

#### B1 - Literature Explorer (ma_literature v2.0)
**Role Definition**
```yaml
name: "Literature Explorer"
legacy_agent: "ma_literature"
phase: "phase_1_discovery"
version: "2.0"

responsibilities:
  - Conduct systematic literature search
  - Map research landscape into lit_map.yaml
  - Identify documented gaps and unexplored mechanisms
  - Synthesize 20+ papers into coherent narrative

deliverables:
  - lit_map.yaml (structured literature matrix)
  - search_strategy.md (reproducible search protocol)

quality_gates:
  - Has literature search been systematic?
  - Are competing mechanisms documented?
  - Clear evidence-base for empirical predictions?

hand_off_to: "B2_Challenger"
```

#### B2 - Challenger / Critical Reviewer (NEW)
**Role Definition**
```yaml
name: "Challenger Researcher"
new_role: true
phase: "phase_1_discovery"
reporting_chain: "Independent of B1"

responsibilities:
  - Red-team B1's literature review
  - Search for contradictory/null findings
  - Check for duplicate hypotheses in SSRN/published
  - Identify potential endogeneity issues
  - Document all conflicts in b2_audit_report.md

deliverables:
  - b2_audit_report.md
  - decision_log entry: "REJECT_HYPOTHESIS" if duplicate found
  
decision_triggers:
  - If is_duplicate_research == true → ROLLBACK to B1
  - If contradictions found → Request B1 revision
  - If coverage incomplete → Escalate to Agent A

escalation_to: "Agent_A"
```

---

### PHASE 2: MAPPING & LOCK

#### C1 - Specification Designer (NEW)
**Role Definition**
```yaml
name: "Research Design Specialist"
new_role: true
phase: "phase_2_lock"

responsibilities:
  - Map H1/H2 to concrete dep/explanatory variables
  - Propose control variable pool
  - Define fixed effects (firm/year/industry)
  - Propose clustering (firm, year, or both)
  - Create sample selection logic
  - Establish lag structures
  - Draft design_lock.yaml

deliverables:
  - design_lock.yaml (draft)
  - specification_memo.md

inputs_from: ["hypotheses.yaml"]
hand_off_to: "C2_Auditor"
```

#### C2 - Data Availability Auditor (ma_data v2.0)
**Role Definition**
```yaml
name: "Data Availability Auditor"
legacy_agent: "ma_data"
version: "2.0"
phase: "phase_2_lock"

responsibilities:
  - Verify each variable in design_lock.yaml exists
  - Check data availability % per source
  - Confirm mouth-to-mouth consistency (variable definitions)
  - Flag any missing data >40%
  - Maintain data_sources_registry.yaml

deliverables:
  - c2_data_availability_report.md
  - data_sources_registry.yaml
  - decision_log: "REQUEST_REVISION" if data_availability < 0.4

decision_triggers:
  - If availability < 0.4 → ROLLBACK to C1 (find proxies)
  - If multiple sources disagree on definition → Escalate
  
quality_gates:
  - Is every variable confirmed obtainable?
  - Is timing alignment feasible?
  - Are access restrictions documented?
```

---

### PHASE 3: DATA ENGINEERING

#### D1 - Data Cleaner / Engineer (ma_cleaning v2.0)
**Role Definition**
```yaml
name: "Data Engineer"
legacy_agent: "ma_cleaning"
version: "2.0"
phase: "phase_3_data_ops"

responsibilities:
  - Implement Merge logic (per design_lock.yaml)
  - Implement Lag operators (event alignment)
  - Implement Winsorization (per design_lock threshold)
  - Execute sample selection filters
  - Create reproducible cleaning script (Python/R)
  - Output clean_data.parquet

deliverables:
  - clean_data.parquet
  - cleaning_code.py (fully commented)
  - d1_cleaning_log.md (merge steps, filter impacts)

constraints:
  - Must follow design_lock.yaml specification exactly
  - Cannot deviate without C2 approval + decision_log entry
  
hand_off_to: "D2_Auditor"
```

#### D2 - Data Quality Auditor (NEW)
**Role Definition**
```yaml
name: "Data Quality Auditor"
new_role: true
phase: "phase_3_data_ops"
reporting_chain: "Independent of D1"

responsibilities:
  - Build sample_loss_tree (track every merge/filter step)
  - Check key uniqueness (no duplicate rows)
  - Analyze missing value distribution (MCAR vs MNAR)
  - Verify Winsorization applied correctly
  - Generate data_audit_scorecard.json
  - Calculate merge_coverage metric

deliverables:
  - data_audit_scorecard.json
  - sample_loss_tree.md
  - missing_pattern_analysis.md

critical_gates:
  - merge_coverage >= 0.85 required to proceed
  - If sample_loss > 30% → ROLLBACK to Phase C (redesign variables)
  - If sample_loss 15-30% → PASS_WITH_WARNING
  
decision_log_output:
  - "AUDIT_RESULT" with pass/fail status
  - "TRIGGER_ROLLBACK" if critical threshold breached

escalation_to: "Agent_A"
```

---

### PHASE 4: ECONOMETRICS

#### E1 - Baseline Regression Runner (ma_regression v2.0)
**Role Definition**
```yaml
name: "Econometrics Runner"
legacy_agent: "ma_regression"
version: "2.0"
phase: "phase_4_econometrics"

responsibilities:
  - Execute baseline OLS/FE/RE per design_lock.yaml
  - Apply specified fixed effects & clustering
  - Produce coefficient tables, std errors, p-values
  - Create publication-ready regression table
  - Document all model specifications

deliverables:
  - baseline_regression.csv
  - regression_tables.xlsx
  - e1_regression_log.md
  - code/run_baseline.py

constraints:
  - No deviation from design_lock.yaml allowed
  - Cannot add/drop variables post-hoc
  - Must report raw + robust SE
  
hand_off_to: "E2_Auditor"
```

#### E2 - Adversarial Econometrics Auditor (NEW)
**Role Definition**
```yaml
name: "Stress Test / Adversarial Auditor"
new_role: true
phase: "phase_4_econometrics"
reporting_chain: "Independent of E1"

responsibilities:
  - Stress Test 1: Re-estimate with alternative clustering levels
  - Stress Test 2: Placebo test (run on pre-treatment period)
  - Stress Test 3: Drop top/bottom 1% outliers & re-estimate
  - Stress Test 4: Subsample robustness (exclude certain industries)
  - Measure coefficient stability (how much do estimates move?)
  - Calculate robustness_pass_rate (% tests passed)
  - Check VIF for multicollinearity
  - Generate regression_scorecard.json

deliverables:
  - regression_scorecard.json (with all test results)
  - stress_test_report.md
  - vif_analysis.csv

critical_gates:
  - If robustness_pass_rate >= 75% → PASS
  - If robustness_pass_rate 50-75% → PASS_WITH_CAVEATS
  - If robustness_pass_rate < 50% → ROLLBACK to design_lock (reconsider ID strategy)
  
decision_log_output:
  - "AUDIT_RESULT" or "TRIGGER_ROLLBACK"
  - Decision matrix: see regression_scorecard.json

escalation_to: "Agent_A"
```

---

### PHASE 5: SYNTHESIS

#### F1 - Economics Narrator (phd_story v2.0)
**Role Definition**
```yaml
name: "Economics Interpreter & Narrative"
legacy_agent: "phd_story"
version: "2.0"
phase: "phase_5_synthesis"

responsibilities:
  - Compare results to H1/H2/H3 in hypotheses.yaml
  - Provide economic interpretation of coefficients
  - Explain magnitude & significance
  - Draft results section of final_report.md
  - Create supporting narrative

deliverables:
  - final_report.md (results section)
  - economic_interpretation.md
  - hypothesis_comparison_table.md

inputs_from: ["hypotheses.yaml", "regression_scorecard.json"]
hand_off_to: "F2_Reviewer"
```

#### F2 - Journal Peer Reviewer / Skeptic (NEW)
**Role Definition**
```yaml
name: "Peer Reviewer / Journal Simulator"
new_role: true
phase: "phase_5_synthesis"
reporting_chain: "Represents external skeptics"

responsibilities:
  - Simulate Top 5 journal peer reviewer
  - Check for endogeneity & omitted variable bias
  - Test for p-hacking (verify design_lock.yaml was frozen)
  - Demand alternative explanations
  - Identify overinterpretation
  - Check if results support H1/H2/H3 or create new questions
  - Draft simulated peer review report

deliverables:
  - f2_peer_review_report.md
  - critique_summary.md
  - alternative_narratives.md

final_checkpoints:
  - Was design_lock.yaml frozen before Phase 3?
  - Were all pre-registered hypotheses tested?
  - Are conclusions justified by evidence?
  - What would reviewers demand?
  
hand_off_to: "Agent_A for final synthesis"
```

---

### Agent A - Master Controller (System Role)

```yaml
name: "Agent A - Econ-OS Master Controller"
system_role: true
across_all_phases: true

responsibilities:
  - Does NOT audit code semantics or statistical methods
  - ONLY checks if Scorecard (期末评分) pass/fail
  - Makes final GATE DECISIONS at end of each phase
  - Implements ROLLBACK LOGIC per rollback_matrix.yaml
  - Logs all decisions to decision_log.jsonl
  - Coordinates escalations to user

phase_1_decision:
  input: "hypotheses.yaml"
  criterion: "gap_defined && h_candidates logically coherent && no duplicates"
  action: "PASS → proceed to Phase 2 OR ROLLBACK_TO_B1"

phase_2_decision:
  input: "design_lock.yaml + c2_audit"
  criterion: "c1_design_ready && c2_audit_passed && merge_coverage_expected > 0.85"
  action: "LOCK design_lock.yaml (immutable) OR ROLLBACK_TO_C1"

phase_3_decision:
  input: "data_audit_scorecard.json"
  criterion: "merge_coverage >= 0.85"
  action: "PASS → Phase 4 OR ROLLBACK_TO_C (reconsider variables)"

phase_4_decision:
  input: "regression_scorecard.json"
  criterion: "robustness_pass_rate >= 0.5"
  action: "PASS → Phase 5 OR ROLLBACK_TO_C (reconsider ID)"

phase_5_decision:
  input: "final_report.md + f2_review"
  criterion: "hypothesis coherence && journal standards met"
  action: "PUBLISH decision_log.jsonl || REVISE"

escalation_to_user:
  condition: "Conflicting recommendations or publication vs redesign decision"
  action: "Present options + historical decision_log context"
```

---

## Implementation Notes

1. **Existing Agents to Transition:**
   - `ma_literature` → Becomes B1_Explorer + Co-develops B2_Challenger role
   - `ma_data` → Becomes C2_Data_Auditor (enhanced with availability checks)
   - `ma_cleaning` → Becomes D1_Engineer (enforces design_lock.yaml compliance)
   - `ma_regression` → Becomes E1_Runner (stripped down to baseline only)

2. **New Agents to Create:**
   - B2: Challenger Researcher (RA role)
   - C1: Specification Designer (PI or senior PhD role)
   - D2: Data Quality Auditor (independent QA role)
   - E2: Adversarial Auditor (senior PhD or domain expert)
   - F2: Journal Reviewer (experienced publication veteran)

3. **Agent A Setup:**
   - Automated decision logic based on scorecard metrics
   - If scorecard meets gate criteria → AUTO_APPROVE
   - If scorecard fails → AUTO_ROLLBACK or escalate to user
   - All decisions logged to decision_log.jsonl with timestamp

4. **No Code Semantics Audit:**
   - Agent A does NOT review whether Python code is correct
   - Agent A does NOT check econometric theory
   - Agent A ONLY checks: Does the scorecard data say we pass/fail?
   - This separation prevents bottlenecks
