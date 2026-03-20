# 经济学实验室角色扮演工作流

这是一个本地、按需触发的研究实验室工作流。你扮演 tenure-track 的青年教师，搭配 Econ-OS 2.0 的 10 个研究角色（文献探索到期刊审稿）推进课题。它借了参考项目的“多角色 + 独立记忆 + 标准流程”骨架，但刻意去掉了 `OpenClaw`、常驻 bot、7x24 守护和 Discord。

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

- `agents/`: 每个角色的 `role.md` 和 `memory.md`
- `projects/`: 每个课题的资料、输出、任务单和运行记录
- `shared-notes/`: 跨课题约定
- `workflow.toml`: 本地模型配置
- `econflow/`: Python CLI

设计来源说明见 `shared-notes/design-sources.md`。

## 我参考了哪些现成模式

- 项目目录和可复现交付：参考了 AEA Data Editor 对 replication package 的要求，以及 World Bank DIME 的 reproducibility protocol
- 任务单和责任链：参考了 Gentzkow & Shapiro 的 project management guide
- RA 常见职责：参考了 Econ RA Guide 和 Northwestern 的 predoc/RA 经验分享

## 快速开始

```powershell
cd D:\econ-research-workflow
python -m econflow status
```

新建课题：

```powershell
python -m econflow new-project "中国最低工资与青年就业" --slug min-wage-youth-employment --question "最低工资提高是否影响青年就业？" --objective "先判断这个题值不值得做"
```

触发 Econ-OS 2.0 全流程：

```powershell
python -m econflow pipeline --project min-wage-youth-employment --preset econ-os-2.0
```

如果只想给某个角色单独任务单：

```powershell
python -m econflow delegate --project min-wage-youth-employment --role b1_explorer --title "补文献矩阵" --description "围绕最低工资与青年就业补 2018 年后的核心文献" --acceptance "按研究问题、数据、识别、结论、局限整理成表"
```

## 预设流程

- `econ-os-2.0`: 10 角色覆盖创意、设计、数据、实证、解释的全流程

## 是否调用模型

默认是 `prompt-only`，只生成任务包和任务单，不调模型。

如果你有本地或远程的 OpenAI-compatible 接口，把 `workflow.toml` 改成：

```toml
[llm]
mode = "openai-compatible"
base_url = "https://api.openai.com/v1"
model = "gpt-4"
api_key_env = "OPENAI_API_KEY"
temperature = 0.2
max_tokens = 4000
```

记得在环境变量里写入 `OPENAI_API_KEY`，然后加 `--execute` 即可。
