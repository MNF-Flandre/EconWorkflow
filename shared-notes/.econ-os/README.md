# Econ-OS 2.0: 经济学自动化研究系统标准 SOP

## 🎯 核心原则

1. **Schema驱动** — 代理间严禁传递纯文本，必须移交标准化文件（YAML/JSON）
2. **非对称校验** — 每个执行角色（1号）必须配备一个独立的反方审计（2号）
3. **设计冻结** — 在进入实证执行前，必须存在不可逾越的"设计锁定点"
4. **Agent A总控** — Master controller 只审 Scorecard（计分卡）是否达标，不审代码语义

---

## 📋 五个阶段 (5-Phase Workflow)

### Phase 1: Discovery Phase - 创意发现与理论对齐
**目标：** 将原始 Idea 转化为具有文献支撑的研究假设

| 角色 | 名称 | 职责 | 输出 |
|------|------|------|------|
| **B1** | 探索者/文献RA | 检索相关文献，产出 lit_map.yaml | `lit_map.yaml` |
| **B2** | 挑战者/审计RA | 审查B1的结论，寻找冲突证据或重复研究 | `b2_audit_report.md` |
| **Agent A** | 总控 | 汇总并生成 hypotheses.yaml | `hypotheses.yaml` 🔓 |

**验收标准:**
- `gap_defined == true`
- `h_candidates` 逻辑自洽
- 无重复研究发现

**失败回滚:** If B2 finds duplicate → ROLLBACK_TO_B1

---

### Phase 2: Mapping & Lock - 研究设计与硬锁定  
**目标：** 定义实证规格，防止后期 p-hacking

| 角色 | 名称 | 职责 | 输出 |
|------|------|------|------|
| **C1** | 设计师 | 将 $H_1, H_2...$ 映射为具体变量，定义数据源 | `design_lock.yaml` (draft) |
| **C2** | 审计员 | 核查变量在数据库中的真实可得性与口径一致性 | `c2_audit_report.md` |
| **Agent A** | 总控 | 生成并锁定 design_lock.yaml | `design_lock.yaml` 🔒 |

**强制内容（锁定项）:**
- 被解释变量定义
- 核心解释变量
- 控制变量池
- 固定效应层级  
- 聚类口径
- 样本筛选逻辑

**禁令:** 一旦锁定，后续 E 阶段不得在无汇报情况下更改此配置

**失败回滚:** If data_availability < 0.4 → ROLLBACK_TO_C1

---

### Phase 3: Data Ops - 数据工程与质量审计
**目标：** 产出"开箱即用"的高质量实证数据集

| 角色 | 名称 | 职责 | 输出 |
|------|------|------|------|
| **D1** | 清洗员 | 编写清洗脚本，执行 Merge、Lag、Winsorize | `clean_data.parquet` |
| **D2** | 质检员 | 运行审计脚本，生成 data_audit_scorecard.json | `data_audit_scorecard.json` |
| **Agent A** | 总控 | 检查 Scorecard 并决定进度 | Gate decision |

**必查项:**
- 样本损失路径（Sample Loss Tree）
- 主键唯一性
- 缺失值分布

**关键指标:**
- `merge_coverage >= 0.85` ✅ PASS
- `0.15 < sample_loss <= 0.30` ⚠️ PASS_WITH_WARNING
- `sample_loss > 0.30` ❌ ROLLBACK_TO_C (重新审视变量定义)

---

### Phase 4: Econometrics - 实证执行与对抗审计
**目标：** 执行估计并经受极端的稳健性考验

| 角色 | 名称 | 职责 | 输出 |
|------|------|------|------|
| **E1** | 运行员 | 按照 design_lock 执行 Baseline Regression | `baseline_regression.csv` |
| **E2** | 对抗者 | 启动"压力测试"包，生成 regression_scorecard.json | `regression_scorecard.json` |
| **Agent A** | 总控 | 判定结果是否稳健 | Gate decision |

**Stress Tests (E2必检项):**
1. **改变聚类层级** — Recluster at different levels, check coeff stability
2. **安慰剂检验** — Placebo in presample period (should be null)
3. **排除极端样本** — Drop top/bottom 1% of outcome, re-estimate
4. **子样本检验** — Subsample robustness (e.g., exclude certain industries)

**关键指标:**
- `robustness_pass_rate >= 0.75` ✅ PASS
- `0.50 <= robustness_pass_rate < 0.75` ⚠️ PASS_WITH_CAVEATS
- `robustness_pass_rate < 0.50` ❌ ROLLBACK_TO_C (重新审视识别策略)

**回滚规则:** If result highly sensitive to spec → ROLLBACK to design_lock

---

### Phase 5: Synthesis - 经济解释与审计轨迹
**目标：** 产出最终结论，并提供全流程审计线索

| 角色 | 名称 | 职责 | 输出 |
|------|------|------|------|
| **F1** | 叙述者 | 对比 $H_1, H_2...$ 解释回归系数的经济含义 | `final_report.md` (draft) |
| **F2** | 审稿员 | 模拟 Top 期刊审稿人，批判内生性处理和过度解释 | `f2_peer_review_report.md` |
| **Agent A** | 总控 | 汇总 final_report.md，附带全流程 decision_log.jsonl | `final_report.md` + audit trail |

---

## 🛠️ 技术实现层：必备组件

### 1. 全程审计日志 (decision_log.jsonl)

每一行必须记录一条决策：

```json
{"timestamp": "2026-03-19T10:30:00Z", "stage": "E2", "action": "TRIGGER_ROLLBACK", "rationale": "Coefficient insignificant after double clustering", "actor": "Agent_A", "robustness_pass_rate": 0.42}
```

**必要字段:**
- `timestamp` — ISO8601 格式
- `stage` — B1/B2/C1/C2/D1/D2/E1/E2/F1/F2
- `action` — REJECT_HYPOTHESIS | REQUEST_REVISION | AUDIT_RESULT | TRIGGER_ROLLBACK | PASS_GATE | ESCALATE_TO_USER
- `rationale` — 人类可读的决策理由
- `actor` — 谁做的决议
- 可选: 相关的指标 (e.g., `p_value`, `merge_coverage`, `robustness_pass_rate`)

---

### 2. 回滚矩阵 (Rollback Logic)

| 触发点 | 触发条件 | 回滚目标 | 动作 |
|-------|--------|--------|------|
| **B2** | `is_duplicate_research == true` | **B1** | 重找gap，另选题目 |
| **C2** | `data_availability < 0.4` | **C1** | 寻找proxy变量 |
| **D2** | `sample_loss_rate > 0.30` | **C** | 放宽筛选或换proxy |
| **E2** | `robustness_pass_rate < 0.50` | **C** | 重审识别策略 |

---

### 3. Agent A 的 Scorecard 判定逻辑

```python
def check_gate(stage, scorecard):
    """Agent A only checks scorecard metrics, never code semantics"""
    
    if stage == "phase_1":
        if scorecard.gap_defined and len(scorecard.h_candidates) > 0:
            return PASS
        else:
            return ROLLBACK_TO_B1
    
    elif stage == "phase_2":
        if scorecard.c1_ready and scorecard.c2_passed:
            return LOCK_SPECIFICATION
        else:
            return ROLLBACK_TO_C1
    
    elif stage == "phase_3":
        if scorecard.merge_coverage >= 0.85:
            return PASS
        elif 0.15 < (1 - scorecard.merge_coverage) <= 0.30:
            return PASS_WITH_WARNING
        else:
            return ROLLBACK_TO_DESIGN_LOCK
    
    elif stage == "phase_4":
        robustness_rate = count_passed_tests(scorecard) / total_tests
        if robustness_rate >= 0.75:
            return PASS
        elif robustness_rate >= 0.50:
            return PASS_WITH_CAVEATS
        else:
            return ROLLBACK_TO_DESIGN_LOCK
    
    elif stage == "phase_5":
        return final_approval(scorecard)
```

---

## 📁 文件系统结构

### 全局 (Shared Templates)
```
shared-notes/.econ-os/
├── schemas/
│   ├── hypotheses.yaml              # Phase 1 output schema
│   ├── design_lock.yaml             # Phase 2 lock schema
│   ├── data_audit_scorecard.json    # Phase 3 scorecard schema
│   ├── regression_scorecard.json    # Phase 4 scorecard schema
│   └── rollback_matrix.yaml         # Rollback decision matrix
├── process_templates.json           # 5-phase workflow definition
├── AGENT_ROLES.md                   # New agent specifications
├── decision_log_infrastructure.py   # Python utilities
├── INTEGRATION_GUIDE.md             # How to integrate
└── README.md (this file)
```

### 项目级 (Per-Project Instantiation)
```
projects/[project-slug]/.econ-os/
├── phase_1/
│   ├── hypotheses.yaml
│   ├── lit_map.yaml
│   ├── b2_audit_report.md
│   └── decision_log.jsonl
├── phase_2/
│   ├── design_lock.yaml (🔒 FROZEN)
│   ├── c2_audit_report.md
│   └── decision_log.jsonl
├── phase_3/
│   ├── clean_data.parquet
│   ├── data_audit_scorecard.json
│   ├── sample_loss_tree.md
│   └── decision_log.jsonl
├── phase_4/
│   ├── baseline_regression.csv
│   ├── regression_scorecard.json
│   ├── stress_test_report.md
│   └── decision_log.jsonl
├── phase_5/
│   ├── final_report.md
│   ├── f2_peer_review_report.md
│   └── decision_log.jsonl
├── decision_log.jsonl               # Master audit trail (all phases)
├── rollback_history.md              # Track all rollbacks
├── project_config.yaml
└── README.md
```

---

## 🔄 典型故障与回滚示例

### 例1：Phase 1 发现重复研究

```
Timeline:
B1 → B2 detects duplicate study "Zhang et al (2024)"
B2 → Log to decision_log: action="REJECT_HYPOTHESIS", hypothesis_id="H1"
Agent A → ROLLBACK_TO_B1
Outcome: B1 must reformulate hypothesis H1, conduct new literature search
```

### 例2：Phase 3 样本大幅流失

```
Timeline:
D1 produces clean_data.parquet (merge coverage 72%)
D2 runs audit → data_audit_scorecard.json
Agent A checks: merge_coverage < 0.85 AND sample_loss > 30%
Agent A → TRIGGER_ROLLBACK("C", reason="Sample loss > 30%")
Outcome: C1+C2 reconvene to loosen sample filters OR find alternative proxy variables
```

### 例3：Phase 4 结果对聚类极度敏感

```
Timeline:
E1 baseline: coeff = 0.025, t-stat = 2.8, p = 0.005
E2 stress test_1: Change to alternative clustering
E2 finds: coeff = 0.015, t-stat = 1.2, p = 0.22 (now insignificant!)
E2 → robustness_pass_rate = 25% (< 50% threshold)
E2 → regression_scorecard.json signals FAIL
Agent A → TRIGGER_ROLLBACK("design_lock", reason="Robustness < 50%")
Outcome: Design A + C2 reconsider fixed effects / identification strategy
```

---

## 🚀 使用流程

### 新项目启动
1. **Run feasibility check** (phd_feasibility) → if PASS:
2. **Initialize .econ-os/** directory → copy from `.econ-os-template/`
3. **Configure project_config.yaml** with PI, timeline, agents
4. **Begin Phase 1:** B1 starts literature search → B2 independent review
5. **Loop:** Each phase completes → Agent A checks scorecard → PASS/ROLLBACK

### 现有项目迁移
See [INTEGRATION_GUIDE.md](./INTEGRATION_GUIDE.md) for step-by-step retroactive migration.

---

## 💡 关键特性

### ✅ 研究诚实性保障
- **Design Lock:** 防止事后p-hacking，固定规格于实验前
- **Audit Trail:** 完整的decision_log.jsonl记录所有决策
- **Pre-registration:** hypotheses.yaml作为预先登记

### ✅ 自动化与可重复性
- **Scorecard-driven:** Agent A不审代码，只审指标
- **Standardized Schemas:** YAML/JSON格式便于版本控制与自动化
- **Rollback Logic:** 自动触发回滚，无需人工干预（可选用户审批）

### ✅ 质量控制  
- **Dual Review:** 每个执行角色配对独立审计角色
- **Stress Tests:** 4-5项压力测试验证结果稳健性
- **Peer Simulation:** F2角色模拟真实期刊审稿

### ✅ 可扩展性
- **Multi-Agent:** 支持团队协作，角色明确
- **Template-based:** 新项目快速启动
- **Version Control:** decision_log支持Git追踪

---

## 📖 相关文件

| 文件 | 用途 |
|------|------|
| [AGENT_ROLES.md](./AGENT_ROLES.md) | 详细的角色定义与职责 |
| [process_templates.json](./process_templates.json) | 5-phase工作流定义 |
| [schemas/](./schemas/) | Scorecard与输出的标准schema |
| [decision_log_infrastructure.py](./decision_log_infrastructure.py) | Python工具库 |
| [INTEGRATION_GUIDE.md](./INTEGRATION_GUIDE.md) | 系统集成指南 |

---

## 🎓 推荐阅读顺序

1. **System Designers:** Read this README → [process_templates.json](./process_templates.json) → [AGENT_ROLES.md](./AGENT_ROLES.md)
2. **Agents:** Read [AGENT_ROLES.md](./AGENT_ROLES.md) → Find your role → Check schemas/ for output format
3. **Project Managers:** Read INTEGRATION_GUIDE.md → Set up project .econ-os/ → Monitor decision_log.jsonl
4. **Sysadmins:** Read [decision_log_infrastructure.py](./decision_log_infrastructure.py) → Deploy gate logic

---

**Version:** Econ-OS 2.0  
**Last Updated:** 2026-03-19  
**Prepared for:** econ-research-workflow

