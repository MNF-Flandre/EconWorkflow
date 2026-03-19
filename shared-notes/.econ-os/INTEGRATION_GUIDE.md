# System Integration Guide for Econ-OS 2.0
# How to integrate the new workflow into existing processes

## 1. File System Changes

### New Global Directories
```
shared-notes/.econ-os/
├── schemas/                          # Global schema definitions
│   ├── hypotheses.yaml
│   ├── design_lock.yaml
│   ├── data_audit_scorecard.json
│   ├── regression_scorecard.json
│   ├── decision_log.jsonl
│   └── rollback_matrix.yaml
├── process_templates.json            # 5-phase workflow definition
├── AGENT_ROLES.md                    # New agent role specifications
├── decision_log_infrastructure.py    # Python utilities for logging
└── README.md
```

### Per-Project Directories
```
projects/[project-slug]/.econ-os/
├── phase_1/
├── phase_2/
├── phase_3/
├── phase_4/
├── phase_5/
├── decision_log.jsonl               # Master audit trail
├── rollback_history.md              # Track all rollbacks
└── project_config.yaml              # Project settings
```

---

## 2. Agent Role Transitions

### Immediate Actions (Existing Agents)

| Agent | Current Role | New Role(s) | Changes Needed |
|-------|--------------|------------|---|
| ma_literature | Literature search | B1 + co-develop B2 | Add B2 as independent reviewer; enhance to produce `lit_map.yaml` |
| ma_data | Data inventory | C2 + C1 liaison | Shift to post-specification validation; add availability % checks |
| ma_cleaning | Data cleaning | D1 | Enforce `design_lock.yaml` compliance; add cleaninng_log.md |
| ma_regression | Regression runs | E1 | Produce only baseline (no post-hoc exps); add regression_log.md |
| phd_feasibility | Scoping | Pre-Phase-1 gate | Run before Phase 1 starts; decide if project is viable |
| phd_story | Narrative | F1 + engage F2 | Add `economic_interpretation.md`; invite F2 review |

### New Agents to Create

| Role | Type | Responsibility | When Active |
|------|------|---|---|
| B2_Challenger | RA | Red-team literature | End of Phase 1 |
| C1_Designer | PhD or Senior RA | Map hypothesis to variables | Phase 2 |
| D2_QA | Senior RA or Postdoc | Data quality audit | Phase 3 |
| E2_Adversarial | PhD or Domain Expert | Stress tests | Phase 4 |
| F2_Reviewer | Publishing experienced | Simulate journal review | Phase 5 |

---

## 3. Integration with Existing Systems

### Entry Point: phd_feasibility as Pre-Gate

**Before Phase 1 starts**, run feasibility check:
```python
# phd_feasibility should validate:
- Is a clear research question defined?
- Is the topic publishable?
- Are preliminary data sources identified?
- Timeline realistic?

# Output: feasibility_report.md
# If FAIL → Do not proceed to Phase 1
# If PASS → Authorize Phase 1 start
```

### Workflow in workflow.toml

Update `workflow.toml` to reference Econ-OS 2.0:

```toml
[workflow]
version = "econ-os-2.0"
description = "5-phase automated economics research pipeline"
process_templates_file = "shared-notes/.econ-os/process_templates.json"
agent_roles_file = "shared-notes/.econ-os/AGENT_ROLES.md"

[phases]
phase_1 = "Discovery"
phase_2 = "Mapping & Lock"
phase_3 = "Data Engineering"
phase_4 = "Econometrics"
phase_5 = "Synthesis"

[automation]
decision_log_enabled = true
auto_rollback_enabled = true
scorecard_validation = "mandatory"
```

---

## 4. Decision Log Monitoring

### Automatic Checking (Optional System)

If system has automation capability, implement cron/webhook:

```python
# Every 6 hours, or on file modification:
def check_phase_completion():
    for project in active_projects:
        scorecard = load_latest_scorecard(project)
        decision = Agent_A.check_gate(scorecard)
        
        if decision == ROLLBACK:
            notify_agents(rollback_target)
            log_decision(project, decision)
```

### Manual Monitoring

If no automation, Agent A should manually:
1. **Check scorecard** at end of each phase
2. **Log decision** to `decision_log.jsonl`
3. **Notify agents** of next phase or rollback

---

## 5. Example: Existing Project Migration

### Scenario
Project "中国资本市场存在动量因子吗" is mid-analysis. How to transition?

**Current State:**
- Literature notes exist
- Data collected
- Preliminary regression run

**Migration Path:**

**Step 1: Retroactive Phase 1 Documentation (1-2 days)**
- Have B1 organize literature into `lit_map.yaml`
- Have B2 review for duplicates → No duplicates found
- Agent A: Approve Phase 1 exit (writing `hypotheses.yaml`)

**Step 2: Lock Current Specification (1 day)**
- Have C1 document current design → `design_lock.yaml` (draft)
- Have C2 verify data availability → Approved
- Agent A: Lock specification (FROZEN)

**Step 3: Audit Current Data (2 days)**
- Have D1 export current data specs→ `d1_cleaning_log.md`
- Have D2 run audit suite → `data_audit_scorecard.json`
- If merge_coverage < 0.85 → ROLLBACK to Phase 2 (reconsider)
- Otherwise → PASS Phase 3

**Step 4: Audit Current Regression (2 days)**
- Have E1 export baseline → `baseline_regression.csv`
- Have E2 run stress tests → `regression_scorecard.json`
- If robustness < 0.5 → ROLLBACK to Phase 2
- Otherwise → PASS Phase 4

**Step 5: Complete Synthesis (3-5 days)**
- Have F1 interpret → `final_report.md` (draft)
- Have F2 review → `f2_peer_review_report.md`
- Agent A → Publish `final_report.md` + `decision_log.jsonl`

**Total: ~1-2 weeks to complete retroactive migration**

---

## 6. Transition Checklist

- [ ] Create `.econ-os/` global schema directory
- [ ] Create `.econ-os-template/` for new projects
- [ ] Update `workflow.toml` with Econ-OS 2.0 reference
- [ ] Brief existing agent teams on new role definitions
- [ ] Identify & train new agents (B2, C1, D2, E2, F2)
- [ ] Set up `decision_log.jsonl` monitoring
- [ ] Audit active projects for compliance
- [ ] Document rollback history for completed projects
- [ ] Test Agent A gate logic on existing data

---

## 7. Questions & Troubleshooting

**Q: My project has published results. Do I need to migrate?**
A: No. Migration applies only to ongoing or new projects.

**Q: Can I skip Phase 2 lock if I "know" my spec is right?**
A: No. Phase 2 lock is mandatory & unforgeable. This is key to research integrity.

**Q: What if E2 stress tests find problems mid-Phase 4?**
A: Log in `decision_log.jsonl` + trigger rollback to Phase 2. Redesign spec.

**Q: Who is Agent A in practice?**
A: Could be PI, senior postdoc, or automated system. Whoever has authority to freeze design_lock & approve gates.

