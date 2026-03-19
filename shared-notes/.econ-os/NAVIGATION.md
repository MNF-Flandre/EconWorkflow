# Econ-OS 2.0 系统导航

## 📍 文件地址

### 全局系统定义 (shared-notes/.econ-os/)

```
.econ-os/
├── README.md                          ⭐ 系统总体设计 (START HERE)
├── QUICK_REFERENCE.md                 📋 快速查询卡
├── AGENT_ROLES.md                     👥 详细角色定义
├── INTEGRATION_GUIDE.md               🔧 系统集成指南
├── decision_log_infrastructure.py     🐍 Python工具与示例
│
├── schemas/                           📋 输出标准与Schema
│   ├── hypotheses.yaml                (Phase 1 输出)
│   ├── design_lock.yaml               (Phase 2 输出 - 冻结点)
│   ├── data_audit_scorecard.json      (Phase 3 输出)
│   ├── regression_scorecard.json      (Phase 4 输出)
│   ├── decision_log.jsonl             (全程审计日志)
│   └── rollback_matrix.yaml           (自动回滚规则)
│
└── process_templates.json             📑 5-Phase工作流定义
```

### 项目模板 (projects/.econ-os-template/)

```
.econ-os-template/
├── README.md                          📖 项目级使用说明
└── project_config.yaml                ⚙️ 项目配置模板
```

---

## 🎯 快速导航

### 我是 PI / 系统设计者
1. 读 `README.md` 理解5个阶段
2. 读 `process_templates.json` 看工作流细节
3. 读 `AGENT_ROLES.md` 理解队伍结构
4. 遵循 `INTEGRATION_GUIDE.md` 部署系统

### 我是 Agent (B1/B2/C1/...)
1. 在 `AGENT_ROLES.md` 找到自己的角色定义
2. 查看对应 Phase 的输出 schema (在 `schemas/`)
3. 读 `QUICK_REFERENCE.md` 理解评判标准
4. 生成输出文件，上传到项目 `.econ-os/phase_X/`

### 我是新项目 PM
1. 复制 `projects/.econ-os-template/` → `projects/[项目slug]/.econ-os/`
2. 编辑 `project_config.yaml` 配置项目信息
3. 分配agents到各个phase
4. 监控 `decision_log.jsonl` 追踪进度

### 我负责系统自动化
1. 研究 `decision_log_infrastructure.py` 中的gate logic
2. 按需部署自动scorecard检查
3. 配置rollback触发器
4. 建立 webhook / cron job 监控decision_log

---

## 📊 阶段对应文件

| Phase | Schema 输入 | Schema 输出 | Scorecard | 关键File |
|-------|-----------|-----------|----------|---------|
| 1️⃣ Discovery | hypotheses.yaml | hypotheses.yaml | gap_defined | `schemas/hypotheses.yaml` |
| 2️⃣ Mapping | hypotheses.yaml | design_lock.yaml | c1+c2 ready | `schemas/design_lock.yaml` |
| 3️⃣ Data | design_lock.yaml | clean_data.parquet | merge_coverage | `schemas/data_audit_scorecard.json` |
| 4️⃣ Econometrics | design_lock.yaml | baseline_regression.csv | robustness_rate | `schemas/regression_scorecard.json` |
| 5️⃣ Synthesis | hypotheses.yaml + results | final_report.md | coherence | decision_log.jsonl |

---

## 🔀 决策流程图

```
START (新项目)
  ↓
  B1 文献搜索 → B2 独立审查
  ↓
  [Phase 1 Score] ← Agent A 检查 hypotheses.yaml
  ├─ PASS → C1 开始设计
  └─ FAIL → ROLLBACK_B1
  ↓
  C1 规格设计 → C2 数据可得性审计
  ↓
  [Phase 2 Score] ← Agent A 检查 design_lock.yaml
  ├─ PASS → 🔒 LOCK specification
  └─ FAIL → ROLLBACK_C1
  ↓
  D1 数据清洗 → D2 质量审计
  ↓
  [Phase 3 Score] ← Agent A 检查 data_audit_scorecard.json
  ├─ merge_coverage ≥ 0.85 → E1 回归
  ├─ 0.15-0.30 → 警告但继续
  └─ > 0.30 → ROLLBACK_C (重设规格)
  ↓
  E1 基准回归 → E2 压力测试
  ↓
  [Phase 4 Score] ← Agent A 检查 regression_scorecard.json
  ├─ robustness ≥ 0.50 → F1 叙事
  └─ < 0.50 → ROLLBACK_C (重审识别策略)
  ↓
  F1 经济解释 → F2 期刊审稿模拟
  ↓
  [Phase 5 Score] ← Agent A 最终汇总
  ├─ OK → 发布 final_report.md + decision_log.jsonl
  └─ 需修改 → Iterate with F1/F2
  ↓
  END (审计报告完成)
```

---

## 🔍 查询表

### 我想知道...

| 问题 | 答案在 |
|------|--------|
| 什么是design lock? | `README.md` Phase 2 部分 |
| 如何回滚? | `QUICK_REFERENCE.md` 回滚决策树 |
| 作为B1我要输出什么? | `AGENT_ROLES.md` → B1部分 → `schemas/hypotheses.yaml` |
| decision_log怎样写? | `schemas/decision_log.jsonl` + `decision_log_infrastructure.py` |
| E2压力测试具体怎么做? | `AGENT_ROLES.md` → E2部分 说明 |
| 现有项目如何迁移? | `INTEGRATION_GUIDE.md` |
| 新项目怎样启动? | `.econ-os-template/README.md` |
| Agent A的决策逻辑? | `decision_log_infrastructure.py` 或 `README.md` 部分 |

---

## 📝 记录与版本控制

### decision_log.jsonl 
**位置:** `projects/[slug]/.econ-os/decision_log.jsonl`
**格式:** JSONL (每行一条决策)
**追踪:** Git 版本控制 (显示所有回滚、批准、拒绝)

### 示例查询
```bash
# 查看所有rollback
grep "TRIGGER_ROLLBACK" decision_log.jsonl

# 查看E2的所有决议
grep '"stage": "E2"' decision_log.jsonl

# 查看Phase 3全史
grep '"stage": "D2"' decision_log.jsonl | tail -5
```

---

## 🚀 部署Checklist

```
系统级 (一次):
├─ [ ] 创建 shared-notes/.econ-os/ 及所有文件
├─ [ ] 创建 projects/.econ-os-template/
├─ [ ] 培训所有agents理解角色
├─ [ ] (可选) 部署自动化gate逻辑

项目级 (每个新研究):
├─ [ ] 复制 .econ-os-template → projects/[slug]/.econ-os/
├─ [ ] 编辑 project_config.yaml
├─ [ ] 分配agents
├─ [ ] B1 开始 Phase 1
└─ [ ] 监控 decision_log.jsonl
```

---

## 💬 常见命令

```bash
# 检查项目stage
cat projects/[slug]/.econ-os/project_config.yaml | grep "phase"

# 查看决策历史
tail -20 projects/[slug]/.econ-os/decision_log.jsonl

# 追踪某个阶段
grep "phase_3" projects/[slug]/.econ-os/decision_log.jsonl

# 检查是否被回滚过
grep "ROLLBACK" projects/[slug]/.econ-os/decision_log.jsonl
```

---

**Econ-OS 2.0 系统完整部署。准备好了吗？**

→ 从 [README.md](./README.md) 开始

