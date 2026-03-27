# 经济学实验室角色扮演工作流

这是一个本地、按需触发的研究实验室工作流。你可以与 Econ-OS 2.0 的 10 个职责覆盖文献探索到期刊审稿的agents一同推进课题。

## 组织图

- 你：PI，负责提 idea、定方向、发任务单
- Econ-OS 2.0 研究角色
- `b1_explorer`: 文献探索者
- `b2_challenger`: 文献挑战者
- `c1_designer`: 规格设计师
- `c2_data_auditor`: 数据可得性审计员
- `d1_engineer`: 数据工程师
- `d2_qa_auditor`: 数据质控审计员
- `e1_runner`: 回归执行者
- `e2_adversarial_auditor`: 稳健性审计员
- `f1_narrator`: 经济解释者
- `f2_journal_reviewer`: 期刊审稿人

## 目录

为什么这些目录存在：
- `shared-notes/.econ-os/` 定义“跨项目不变”的协议与流程约束。
- `projects/` 承载“项目实例化后”的阶段产物与任务票据。
- `econflow/` 把协议落成可执行 CLI / Web UI，提供最小运行壳层。

## Quick Start / 快速开始

### 0) 安装

```bash
cd /home/runner/work/EconWorkflow/EconWorkflow
python -m pip install -e .
```

### 1) 查看工作区状态（默认 prompt-only，无需 API）

```bash
python -m econflow status
```

### 2) 新建一个项目

```bash
python -m econflow new-project "中国最低工资与青年就业" \
  --slug min-wage-youth-employment \
  --question "最低工资提高是否影响青年就业？" \
  --objective "先判断这个题值不值得做"
```

### 3) 运行预设 pipeline（只生成任务包，不调用模型）

```bash
python -m econflow pipeline --project min-wage-youth-employment --preset econ-os-2.0
```

### 4) 可选：调用模型执行

仅当你需要真实模型响应时：
1. 将 `workflow.toml` 中 `[llm].mode` 从 `prompt-only` 改为 `openai-compatible`
2. 配置 `OPENAI_API_KEY`
3. 在命令追加 `--execute`

## Typical Workflow / 典型使用路径

1. 初始化环境并确认 `status` 可用。  
2. 使用 `new-project` 创建课题目录。  
3. 用 `status --project <slug>` 查看阶段和交付进度。  
4. 用 `pipeline` 跑整套流程，或用 `delegate` 给单角色发任务。  
5. 在 `projects/<slug>/phase_*` 查看各阶段输出与 scorecard。  
6. 通过 `decision_log.jsonl` 追踪关键决策。  
7. 若触发回滚条件，回到对应阶段修订后再推进。  

## What this repo currently includes / does not include

### Includes
- Econ-OS 2.0 角色体系与默认角色卡
- 5 阶段流程模板与 pipeline 入口
- Schema 协议文件（hypotheses / design lock / scorecards / decision log / rollback）
- 本地 CLI 与本地 Web UI 壳层
- 项目模板与票据化任务委派机制

### Does not include
- 任何个人私有项目、私有数据或私有 API 凭据
- 托管式在线服务（SaaS）
- 完整封装的“全自动计量执行引擎”
- 生产级多租户权限与云端编排基础设施

## Current Status

- **Maturity:** alpha  
- **Operating model:** local-first, on-demand  
- **Workflow shell:** available  
- **Execution depth:** evolving

## Related Docs

- `shared-notes/.econ-os/README.md`：Econ-OS 2.0 协议层总览
- `shared-notes/.econ-os/AGENT_ROLES.md`：角色职责与输入输出契约
- `shared-notes/.econ-os/INTEGRATION_GUIDE.md`：集成与迁移指引
- `projects/.econ-os-template/README.md`：项目模板使用说明
