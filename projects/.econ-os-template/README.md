# Project-Level Econ-OS 2.0 Initialization
# Copy this template to [project-slug]/.econ-os/ when starting a new research cycle

## Directory Structure
```
[project-slug]/
├── .econ-os/
│   ├── phase_1/
│   │   ├── hypotheses.yaml          # Output: Agent A synthesis of B1+B2
│   │   ├── lit_map.yaml             # Output: B1 literature matrix
│   │   ├── b2_audit_report.md       # Output: B2 critical review
│   │   └── decision_log.jsonl       # Phase 1 decisions
│   │
│   ├── phase_2/
│   │   ├── design_lock.yaml         # 🔒 FROZEN - Core specification
│   │   ├── c2_data_availability.md  # Output: C2 audit
│   │   ├── data_sources_registry.yaml
│   │   └── decision_log.jsonl
│   │
│   ├── phase_3/
│   │   ├── clean_data.parquet       # Output: D1 data engineering
│   │   ├── data_audit_scorecard.json # Output: D2 quality audit
│   │   ├── sample_loss_tree.md
│   │   ├── d1_cleaning_log.md
│   │   └── decision_log.jsonl
│   │
│   ├── phase_4/
│   │   ├── baseline_regression.csv  # Output: E1 baseline
│   │   ├── regression_scorecard.json # Output: E2 stress tests
│   │   ├── stress_test_report.md
│   │   └── decision_log.jsonl
│   │
│   ├── phase_5/
│   │   ├── final_report.md          # Output: F1+F2+Agent A
│   │   ├── f2_peer_review_report.md
│   │   ├── economic_interpretation.md
│   │   └── decision_log.jsonl
│   │
│   ├── decision_log.jsonl           # 🔓 Complete audit trail (all phases)
│   ├── rollback_history.md          # Track any rollbacks
│   ├── project_config.yaml          # Project-specific settings
│   └── README.md
```

## Project Config Template

Create `[project-slug]/.econ-os/project_config.yaml`:

```yaml
# Econ-OS 2.0 Project Configuration
project_slug: "momentum-factor-china"
research_title: "Does momentum exist in Chinese stock markets?"
pi_name: "张三"
created_at: "2026-03-19"

phase_timeline:
  phase_1_discovery:
    start_date: "2026-03-19"
    end_date: "2026-04-09"
    responsible_agents: ["B1_ma_literature", "B2_challenger_ta"]
  
  phase_2_lock:
    start_date: "2026-04-10"
    end_date: "2026-04-24"
    responsible_agents: ["C1_designer_phd", "C2_ma_data"]
    freeze_point: "design_lock.yaml"
  
  phase_3_data:
    start_date: "2026-04-25"
    end_date: "2026-05-23"
    responsible_agents: ["D1_ma_cleaning", "D2_qa_auditor"]
  
  phase_4_estimation:
    start_date: "2026-05-24"
    end_date: "2026-06-14"
    responsible_agents: ["E1_ma_regression", "E2_adversarial_phd"]
  
  phase_5_synthesis:
    start_date: "2026-06-15"
    end_date: "2026-06-29"
    responsible_agents: ["F1_phd_story", "F2_journal_reviewer"]

rollback_thresholds:
  data_availability_min: 0.40        # Phase 2-3
  merge_coverage_min: 0.85           # Phase 3-4
  sample_loss_max_pct: 0.30          # Phase 3
  robustness_pass_rate_min: 0.50     # Phase 4-5

contact_info:
  pi_email: "zhangsan@univ.ac.cn"
  agent_b1: "ma_literature@agent.local"
  agent_c1: "phd_designer@agent.local"
  escalation_email: "research-chair@univ.ac.cn"

audit_trail_enabled: true
```

## Template Files by Phase

### PHASE 1: hypothesis_template.yaml
```yaml
# Use this template to structure Phase 1 output
research_background: |
  1-2 paragraph background on why this research matters
  
research_question: "Do momentum effects exist in Chinese equity markets?"

gap_identification: |
  What gap in prior literature does this research address?
  Cite 3-5 papers that have NOT answered this question.

h_candidates:
  
  - hypothesis_id: "H1_momentum_positive"
    statement: "Past returns positively predict future returns over 3-12 month horizons"
    mechanism: "Behavioral underreaction & market microstructure lags"
    
    supporting_evidence:
      - "Jegadeesh & Titman (1993): US momentum"
      - "Novy-Marx & Velikov (2016): Momentum profits after costs"
    
    empirical_prediction: |
      Top portfolio (highest past returns) will outperform 
      bottom portfolio by 2-5% annualized in Chinese stocks
    
    competing_explanations:
      - "Explanation: Mean reversion dominates long forward horizon"
        "Ruling out: Different test window than J&T; use 3-12 months"
    
    status: "active"

  - hypothesis_id: "H2_size_effect"
    statement: "Momentum premium larger in small-cap stocks"
    mechanism: "Reduced analyst coverage, slower info diffusion"
    status: "deferred"

  - hypothesis_id: "H3_already_published"
    statement: "[Some hypothesis from Bender et al 2019]"
    status: "rejected"
    rejection_note: "Exact hypothesis already tested - found in duplicate check"
```

### PHASE 2: design_lock_template.yaml
```yaml
# Locked specification - DO NOT CHANGE after Phase 2→Phase 3 transition
LOCKED_AT: "2026-04-24T17:00:00Z"
LOCKED_BY: "Agent_A + PI_approval"

# DEPENDENT VARIABLE
dependent_variable:
  name: "SixMonthHoldingReturn"
  definition: |
    Buy past winner/loser portfolio on month t, 
    hold for 6 months, measure return
  source: "China Stock Market & Accounting Research databank"
  sample_period: "2010-01 to 2021-12"

# MAIN EXPLANATORY VARIABLES  
main_explanatory_variables:
  - var_id: "PastReturnMomentum"
    name: "Past 12-month return (t-12 to t-1)"
    construction: "Cumulative return, skip 1 month (t-2 to t-13)"
    lag_structure: 0  # Contemporaneous with return measurement start

# CONTROLS
controls_pool:
  - var_id: "FirmSize"
    name: "Market cap (log)"
    rationale: "Omitted variable bias control"
  - var_id: "BookToMarket"
    name: "Book/market ratio"

# SPECIFICATION
specification:
  estimator: "OLS"
  fixed_effects:
    - effect_type: "time"
      dimension: "year"
    - effect_type: "time"  
      dimension: "month"
  clustering:
    - "firm"

# SAMPLE SELECTION
sample_selection:
  - rule: "Drop financials (sector=banking)"
    expected_loss_pct: 2.5
  - rule: "Drop observations with missing returns"
    expected_loss_pct: 5.0

phase_2_approval_gate: "LOCKED"
```

### PHASE 3: data_audit_template.json
```json
{
  "phase_3_checkpoint": "data_audit_scorecard.json",
  "overall_status": "PASS_OR_ROLLBACK",
  
  "sample_loss_breakdown": {
    "initial_universe": 500000,
    "after_merge_csmar_returns": {
      "count": 485000,
      "loss_pct": 3.0
    },
    "after_sector_filter": {
      "count": 472550,
      "loss_pct": 2.7
    },
    "final_sample": {
      "count": 472550,
      "total_loss_pct": 5.5,
      "acceptable": true
    }
  },
  
  "merge_coverage": 0.945,
  "threshold": 0.85,
  "passes_threshold": true
}
```

### PHASE 4: regression_audit_template.json
```json
{
  "baseline_result": {
    "coefficient_X1": 0.0245,
    "std_error": 0.0089,
    "t_stat": 2.75,
    "p_value": 0.006
  },
  
  "stress_tests": {
    "test_alternative_clustering": {
      "coeff_with_year_clustering": 0.0247,
      "coeff_with_firm_clustering": 0.0243,
      "movement_pct": 0.8,
      "passes": true
    }
  },
  
  "overall_robustness_pass_rate": 0.75,
  "threshold": 0.50,
  "decision": "PASS"
}
```

## Automated Rollback Triggers (Agent A)

Agent A monitors scorecard files and auto-triggers:

```python
# Pseudo-code decision logic

if phase == "phase_1":
    if hypotheses.gap_defined and len(hypotheses.h_candidates) > 0:
        approve_phase_1()
    else:
        trigger_rollback("B1", reason="Incomplete gap identification")

elif phase == "phase_2":
    if design_lock.c1_ready and design_lock.c2_passed:
        freeze_design_lock()
    else:
        trigger_rollback("C1", reason="Data availability < 40%")

elif phase == "phase_3":
    if data_scorecard.merge_coverage >= 0.85:
        approve_phase_3()
    elif 0.15 < sample_loss <= 0.3:
        approve_with_warning()
    else:
        trigger_rollback("C", reason="Sample loss > 30%")

elif phase == "phase_4":
    robustness_rate = count_passed_tests() / total_tests
    if robustness_rate >= 0.5:
        approve_phase_4()
    else:
        trigger_rollback("design_lock", reason="Robustness < 50%")

elif phase == "phase_5":
    final_approval(hypotheses, results, f2_review)
```

## Usage Instructions

1. **When starting new project:**
   - Copy this entire `.econ-os-template/` folder to `[project-slug]/.econ-os/`
   - Edit `project_config.yaml` with project-specific info
   - Create `phase_1/` subdirectory

2. **For each phase completion:**
   - Agent generates output files per specs above
   - Output automatically logged to `phase_X/decision_log.jsonl`
   - Agent A checks scorecard file for pass/fail
   - If pass → move to next phase
   - If fail → log rollback in decision_log & notify agents

3. **Audit trail:**
   - All decisions recorded in master `decision_log.jsonl`
   - Search by `stage`, `action`, or `timestamp`
   - Enables reproducibility & publication transparency

4. **Reverting changes post-freeze:**
   - design_lock.yaml is immutable after Phase 2→3
   - Any change requires entry in `decision_log.jsonl` with rationale
   - Only Agent A + PI can authorize modification
