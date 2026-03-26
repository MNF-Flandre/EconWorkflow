# EconWorkflow (Econ-OS 2.0, alpha)

EconWorkflow 是一个**本地运行、按需触发**的经济学研究工作流系统，面向希望把研究过程结构化、可追踪化的 PI / RA 团队与独立研究者。  
它的核心是 **Schema 驱动 + 阶段化状态管理 + 多角色协作**，用于统一研究流程与交付物。  
它**不是**托管式 AutoML 平台、不是云端代理编排服务，也不是“一键产出论文”的黑盒工具。

> Public 版本聚焦工作流框架与协议层（角色、流程、schema、状态），不包含任何个人私有研究项目实例或私有数据。

## Key Features / 核心特性

- **Supervisor-led orchestration**：以 PI / Supervisor 视角组织任务，角色分工明确，支持 `pipeline` 与 `delegate`。
- **Standardized phase structure**：固定 5 阶段（Discovery → Design Lock → Data Ops → Econometrics → Synthesis）。
- **Schema-based handoff**：关键阶段输出采用 YAML / JSON / JSONL 协议，便于审阅、复核与自动化检查。
- **Decision logs and rollback**：通过 `decision_log.jsonl` 记录关键决策，按规则触发回滚。
- **Prompt-only default, local-first**：默认 `prompt-only`，首次体验无需 API Key；仅在 `--execute` 时调用模型。
- **CLI + Web UI**：CLI 负责可脚本化执行，Web UI 负责状态可视化与本地操作入口。

## Project Structure / 仓库结构

```text
EconWorkflow/
├─ econflow/                     # CLI 与本地 Web UI 实现
├─ agents/                       # 角色定义（role/memory/profile/card）
├─ projects/                     # 课题目录（含 .econ-os-template 模板）
├─ shared-notes/                 # 跨课题共享约定
│  └─ .econ-os/                  # Econ-OS 2.0 协议层文档、schemas、流程模板
├─ workflow.toml                 # 工作流与默认 LLM 行为配置
└─ pyproject.toml                # Python 包元信息与入口脚本
```

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
