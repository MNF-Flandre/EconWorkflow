# Econ-OS 2.0 Agent Role Mapping

**激活日期:** 2026-03-19  
**系统版本:** econ-os-2.0  
**状态:** 🟢 ACTIVE

---

## 角色映射表 (Agent Role Mapping)

### Phase 1: Discovery (文献搜索与理论对齐)

| 新角色ID | 新角色名 | Agent目录 | 状态 |
|---------|--------|------|------|
| **B1** | Explorer / Literature RA | `agents/b1_explorer/` | ✅ 内置 |
| **B2** | Challenger / Auditor | `agents/b2_challenger/` | ✅ 内置 |

**B1 职责:** 
- 系统文献搜索 → `lit_map.yaml`
- 输出: `phase_1/lit_map.yaml`

**B2 职责 (新):**
- 独立审查B1结果，寻找重复研究
- 输出: `phase_1/b2_audit_report.md`
- 失败触发: `ROLLBACK_TO_B1`

---

### Phase 2: Mapping & Lock (规格设计与冻结)

| 新角色ID | 新角色名 | Agent目录 | 状态 |
|---------|--------|------|------|
| **C1** | Designer | `agents/c1_designer/` | ✅ 内置 |
| **C2** | Data Auditor | `agents/c2_data_auditor/` | ✅ 内置 |

**C1 职责 (新):**
- 将假设映射为具体变量
- 定义样本选择、固定效应、聚类
- 产出: `phase_2/design_lock.yaml` 🔒

**C2 职责:**
- 验证数据可得性 > 40%
- 产出: `phase_2/c2_data_availability_report.md`

**关键:** design_lock.yaml 在此冻结，之后Phase 3-5不可更改

---

### Phase 3: Data Ops (数据清洗与质量审计)

| 新角色ID | 新角色名 | Agent目录 | 状态 |
|---------|--------|------|------|
| **D1** | Engineer | `agents/d1_engineer/` | ✅ 内置 |
| **D2** | QA Auditor | `agents/d2_qa_auditor/` | ✅ 内置 |

**D1 职责:**
- 执行清洗脚本: Merge, Lag, Winsorize
- 遵守 design_lock.yaml
- 产出: `phase_3/clean_data.parquet`

**D2 职责 (新):**
- 运行质量审计: sample loss tree, key uniqueness, missing patterns
- 产出: `phase_3/data_audit_scorecard.json`
- 通过条件: `merge_coverage >= 0.85`
- 失败触发: `ROLLBACK_TO_PHASE_C`

---

### Phase 4: Econometrics (回归与压力测试)

| 新角色ID | 新角色名 | Agent目录 | 状态 |
|---------|--------|------|------|
| **E1** | Regression Runner | `agents/e1_runner/` | ✅ 内置 |
| **E2** | Adversarial Auditor | `agents/e2_adversarial_auditor/` | ✅ 内置 |

**E1 职责:**
- 执行基准回归 (OLS/FE/RE)
- 遵守 design_lock.yaml
- 产出: `phase_4/baseline_regression.csv`

**E2 职责 (新):**
- 启动4项压力测试 (clustering, placebo, outliers, subsample)
- 计算 robustness_pass_rate
- 产出: `phase_4/regression_scorecard.json`
- 通过条件: `robustness_pass_rate >= 0.50`
- 失败触发: `ROLLBACK_TO_DESIGN_LOCK`

---

### Phase 5: Synthesis (经济解释与期刊模拟)

| 新角色ID | 新角色名 | Agent目录 | 状态 |
|---------|--------|------|------|
| **F1** | Narrator | `agents/f1_narrator/` | ✅ 内置 |
| **F2** | Journal Reviewer | `agents/f2_journal_reviewer/` | ✅ 内置 |

**F1 职责:**
- 解释系数的经济含义
- 对比 hypotheses.yaml 与结果
- 产出: `phase_5/final_report.md` (draft)

**F2 职责 (新):**
- 模拟Top期刊审稿人进行批评
- 检查内生性处理、过度解释
- 产出: `phase_5/f2_peer_review_report.md`

---

### 系统级角色

| 角色 | 名称 | 职责 | 输入 |
|------|------|------|------|
| **Agent A** | Master Controller | 审查scorecard，决定PASS/ROLLBACK | 各phase的scorecard.json |
| **System** | Decision Logger | 记录所有决策到 decision_log.jsonl | 各agent的日志 |

---

## 使用说明 (How to Use)

### 1. webui中查看工作流

访问 http://localhost:5010 ，应该看到：
- **工作流版本:** Econ-OS 2.0
- **活跃Phase:** (当前项目所在的phase)
- **Agents列表:** B1, B2, C1, C2, D1, D2, E1, E2, F1, F2

### 2. 创建新项目并应用Econ-OS 2.0

```bash
# 项目会自动从 projects/.econ-os-template/ 初始化
# 包含5个phase目录和project_config.yaml
```

### 3. 监控决策日志

每个项目都会生成:
- `projects/[slug]/.econ-os/decision_log.jsonl` — 完整审计日志
- 每行一条JSON决策 (timestamp, stage, action, rationale)

### 4. 回滚触发

系统自动检查各phase的scorecard：
- Phase 1: `hypotheses.yaml` 中 `gap_defined == true`
- Phase 2: `design_lock.yaml` 中 `c1_ready && c2_passed`
- Phase 3: `data_audit_scorecard.json` 中 `merge_coverage >= 0.85`
- Phase 4: `regression_scorecard.json` 中 `robustness_pass_rate >= 0.50`

---

## 新建的Agent角色 (需要分配人员)

| 角色 | 类型 | 建议人选 | 优先级 |
|------|------|--------|--------|
| **B2 Challenger** | 文献红队 | 具备系统文献审查经验的研究者 | 🔴 高 |
| **C1 Designer** | 规格设计师 | 有设计/识别经验的研究者 | 🔴 高 |
| **D2 QA Auditor** | 数据质检 | 有数据审计背景的研究者 | 🟡 中 |
| **E2 Adversarial** | 计量审计员 | 熟练稳健性压力测试的研究者 | 🔴 高 |
| **F2 Journal Reviewer** | 期刊模拟 | 发表经验丰富的评审人 | 🟡 中 |

---

## 配置检查清单

- ✅ workflow.toml 已更新为 econ-os-2.0
- ✅ process_state.json 已指向新工作流
- ✅ shared-notes/.econ-os/ 包含所有schema和process_templates.json
- ⏳ webui.py 可能需要小更新（可选，现有功能应兼容）
- ⏳ agents目录中新角色配置（可后续添加）

---

**下一步:** 启动webui并在项目中测试Econ-OS 2.0工作流

