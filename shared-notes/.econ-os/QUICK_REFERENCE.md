# Econ-OS 2.0 快速参考卡 (Quick Reference)

## 五阶段一览表

| Phase | 名称 | 执行者 | 关键输出 | 通过指标 | 失败触发 |
|-------|------|--------|--------|--------|---------|
| **1** | Discovery | B1 + B2 | `hypotheses.yaml` | gap_defined=true | ROLLBACK_B1 |
| **2** | Mapping & Lock | C1 + C2 | `design_lock.yaml` 🔒 | c1+c2 approve | ROLLBACK_C1 |
| **3** | Data Ops | D1 + D2 | `data_audit_scorecard.json` | merge_coverage≥0.85 | ROLLBACK_C |
| **4** | Econometrics | E1 + E2 | `regression_scorecard.json` | robustness≥0.50 | ROLLBACK_C |
| **5** | Synthesis | F1 + F2 | `final_report.md` + audit trail | h_coherent | REVISION |

---

## 新角色速览

```
✍️ 执行者 (Producer)      🔍 审计者 (Auditor)       🎛️ 控制者 (Gate)
├─ B1: Literature        ├─ B2: Challenger       ├─ Agent A: Every phase
├─ C1: Designer          ├─ C2: Data Auditor     │
├─ D1: Engineer          ├─ D2: QA Auditor       │
├─ E1: Runner            ├─ E2: Adversarial      │
├─ F1: Narrator          ├─ F2: Reviewer         │
```

---

## 回滚决策树

```
B2: is_duplicate_research  
└─ YES → ROLLBACK_B1 (Reformulate hypothesis)

C2: data_availability < 0.40
└─ YES → ROLLBACK_C1 (Find proxies)

D2: sample_loss > 30%
├─ YES → ROLLBACK_C (Loosen filters / change variables)
├─ 15-30% → PASS_WITH_WARNING
└─ <15% → PASS

E2: robustness_pass_rate < 50%
├─ YES → ROLLBACK_C (Reconsider ID)
├─ 50-75% → PASS_WITH_CAVEATS
└─ >75% → PASS
```

---

## Scorecard 检查清单

每阶段末，Agent A 检查:

### Phase 1
- [ ] `hypotheses.gap_defined == true`
- [ ] `hypotheses.h_candidates.length > 0`
- [ ] B2 found no duplicates

### Phase 2
- [ ] `design_lock.c1_design_ready == true`
- [ ] `design_lock.c2_audit_passed == true`
- [ ] All variables confirmed obtainable

### Phase 3
- [ ] `data_audit_scorecard.merge_coverage >= 0.85`
- [ ] Sample loss tree documented
- [ ] No key duplicates

### Phase 4
- [ ] E1 baseline produced
- [ ] E2 stress tests completed
- [ ] `regression_scorecard.robustness_pass_rate >= 0.50`

### Phase 5
- [ ] F1 narrative complete
- [ ] F2 peer review complete
- [ ] decision_log.jsonl exported

---

## 文件模板速查

| 要找 | 位置 | 模板 |
|------|------|------|
| 假设定义 | `schemas/hypotheses.yaml` | YAML schema |
| 规格冻结 | `schemas/design_lock.yaml` | YAML schema |
| 数据审计 | `schemas/data_audit_scorecard.json` | JSON schema |
| 回归检验 | `schemas/regression_scorecard.json` | JSON schema |
| 决策日志 | `schemas/decision_log.jsonl` | JSONL format |
| 回滚矩阵 | `schemas/rollback_matrix.yaml` | YAML rules |

---

## 项目初始化步骤

```bash
# 1. 创建项目目录
mkdir projects/[project-slug]

# 2. 复制模板
cp -r projects/.econ-os-template projects/[project-slug]/.econ-os

# 3. 配置项目
edit projects/[project-slug]/.econ-os/project_config.yaml

# 4. 启动 Phase 1
# B1 begins literature research
# B2 assigned as independent reviewer

# 5. 监控 decision_log.jsonl
tail -f projects/[project-slug]/.econ-os/decision_log.jsonl
```

---

## Agent A 决策 Pseudo-Code

```python
# 在每个阶段末自动运行

def phase_gate(current_phase, scorecard_path):
    scorecard = load_json_or_yaml(scorecard_path)
    
    metrics = extract_metrics(scorecard)
    
    decision = apply_thresholds(current_phase, metrics)
    
    log_to_decision_log(decision)
    
    if decision == PASS:
        notify_next_agents()
    elif decision == ROLLBACK:
        notify_rollback_target_agents()
        escalate_if_needed(user)
    
    return decision
```

---

## 常见问题

### Q: 能跳过Phase 2 的design lock吗?
**A:** No. Design lock at end of Phase 2 is **mandatory and unforgeable**. This is core to preventing p-hacking.

### Q: Phase 4 失败了怎么办?
**A:** If `robustness_pass_rate < 0.50`, automatically ROLLBACK to Phase 2. C1+C2 redesign identification strategy, then restart from Phase 3.

### Q: decision_log.jsonl 怎样格式化?
**A:** 每行一个JSON对象，包含 `timestamp`, `stage`, `action`, `rationale`, `actor`, 可选指标。See `decision_log_infrastructure.py`.

### Q: Agent A 需要审查代码质量吗?
**A:** **No.** Agent A only checks scorecard metrics. It never reviews code semantics or econometric correctness. This prevents bottlenecks.

### Q: 现有项目能迁移吗?
**A:** Yes. See [INTEGRATION_GUIDE.md](./INTEGRATION_GUIDE.md) for retroactive migration steps (takes 1-2 weeks).

---

## 系统部署清单

- [ ] 创建 `shared-notes/.econ-os/` 目录结构
- [ ] 上传所有 schemas/, process_templates.json, AGENT_ROLES.md
- [ ] 创建 `projects/.econ-os-template/` 模板
- [ ] 更新 `workflow.toml` 引用 Econ-OS 2.0
- [ ] 培训所有agents了解新角色
- [ ] 部署 decision_log_infrastructure.py (可选自动化)
- [ ] 在Git中追踪 decision_log.jsonl (审计日志)
- [ ] 测试Phase 1-5流程一次

---

**快速反查:** 遇到 [问题类型]? → 见[相关文件](./README.md)

