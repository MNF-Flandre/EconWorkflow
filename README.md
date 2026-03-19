# 经济学实验室角色扮演工作流

这是一个本地、按需触发的研究实验室工作流。你扮演 tenure-track 的青年教师，下面是一层博士生组长，再往下是一层硕士生 RA。它借了参考项目的“多角色 + 独立记忆 + 标准流程”骨架，但刻意去掉了 `OpenClaw`、常驻 bot、7x24 守护和 Discord。

## 组织图

- 你：PI，负责提 idea、定方向、发任务单
- 博士生组长
- `phd_feasibility`: 评估题目值不值得做
- `phd_data`: 判断数据和识别能不能做
- `phd_story`: 搭故事线、拆执行包
- 硕士生 RA
- `ma_literature`: 补文献矩阵
- `ma_data`: 拉数据、记数据清单
- `ma_cleaning`: 做清洗与合并日志
- `ma_regression`: 跑回归执行清单
- `ma_replication`: 做复核、表图与交付 checklist

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

这些来源没有直接规定“博士生管硕士生”的层级，所以这部分是我基于你给的设定做的组织化推断。

## 快速开始

```powershell
cd D:\econ-research-workflow
python -m econflow status
```

新建课题：

```powershell
python -m econflow new-project "中国最低工资与青年就业" --slug min-wage-youth-employment --question "最低工资提高是否影响青年就业？" --objective "先判断这个题值不值得做"
```

让 3 个博士生先做委员会评估：

```powershell
python -m econflow pipeline --project min-wage-youth-employment --preset committee-review
```

如果博士生认为值得做，再给硕士生发任务：

```powershell
python -m econflow delegate --project min-wage-youth-employment --role ma_literature --title "补文献矩阵" --description "围绕最低工资与青年就业补 2018 年后的核心文献" --acceptance "按研究问题、数据、识别、结论、局限整理成表"
```

对某个角色单独生成一份任务包：

```powershell
python -m econflow run --project min-wage-youth-employment --role phd_data
```

## 预设流程

- `committee-review`: 3 个博士生先评估想法、数据和故事
- `ra-sprint`: 5 个硕士生执行文献、数据、清洗、回归和复核
- `faculty-lab`: 从博士生评估一路推到硕士生执行

## 是否调用模型

默认是 `prompt-only`，只生成任务包和任务单，不调模型。

如果你有本地或远程的 OpenAI-compatible 接口，把 `workflow.toml` 改成：

```toml
[llm]
mode = "openai-compatible"
base_url = "http://localhost:1234/v1"
model = "your-local-model"
api_key_env = "OPENAI_API_KEY"
temperature = 0.2
max_tokens = 4000
```

然后加 `--execute` 即可。
