# 设计来源说明

这个工作流不是凭空捏出来的，主要借了下面几类现成模式。

## 1. 项目目录和可复现交付

- AEA Data Editor, "Replication packages":
  https://aeadataeditor.github.io/
- World Bank DIME Analytics, "Research and reproducibility":
  https://dimewiki.worldbank.org/Reproducible_Research
- Black Research Group, "my-project":
  https://blackresearchgroup.github.io/research-guide/research-flow/

我据此把课题目录拆成了 `data/raw`、`data/processed`、`analysis/code`、`analysis/tables`、`analysis/figures`、`outputs` 和 `runs`。

## 2. 任务单和责任链

- Gentzkow and Shapiro, "Coding, Writing, and Working More Efficiently":
  https://web.stanford.edu/~gentzkow/research/CodeAndData.pdf

这份 guide 里强调任务管理系统、责任明确和可追踪状态，所以我给项目加了 `tickets/open` 和 `tickets/done`，并做了 `delegate` 命令。

## 3. RA 常见工作内容

- Econ RA Guide:
  https://www.econraguide.com/
- Northwestern University, "Predoc as a research assistant":
  https://sites.northwestern.edu/koki/predoc-as-a-research-assistant/

这些来源都把文献搜集、数据整理、编程、回归和复现当作 RA 的高频工作。

## 4. 我自己做的推断

下面这部分不是某个来源直接规定的，而是根据你的设定做的组织化推断：

- 你扮演 tenure-track 青年教师 PI
- 博士生负责题目筛选、数据与识别评估、故事线和任务拆包
- 硕士生负责文献、数据、清洗、回归和复核等执行层工作

这套分工更像一个有层级的研究实验室，而不是平铺的多 agent。
