# Econ-OS 2.0 Deployment Summary (Public Repository)

本文件用于说明当前 public 仓库已交付的能力边界，帮助外部读者判断可用范围。

## Current Scope

当前仓库是 **local-first、on-demand、alpha** 的工作流壳层，重点在协议与流程一致性：
- 5 阶段流程模板
- 10 个 Econ-OS 2.0 角色定义
- schema 驱动交接与 scorecard 门控
- CLI + Web UI 的本地入口

## Delivered Components

- `README.md`: 对外首页、定位与最小上手路径
- `workflow.toml`: 默认运行配置（含 prompt-only 默认）
- `shared-notes/.econ-os/AGENT_ROLES.md`: 角色契约
- `shared-notes/.econ-os/INTEGRATION_GUIDE.md`: 接入与迁移说明
- `shared-notes/.econ-os/schemas/*`: 协议文件
- `projects/.econ-os-template/`: 项目模板

## Validation Status (Documentation-level)

- 术语统一：Econ-OS 2.0 / prompt-only / pipeline / delegate / scorecard / rollback
- 默认行为统一：首次体验无需 API key；仅 `--execute` + openai-compatible 才调用模型
- 路径统一：流程模板与角色定义路径与 `workflow.toml` 对齐

## Not Included in Public Scope

- 私有研究数据与私有项目实例
- 托管式在线服务或多租户权限系统
- 已封装的全自动计量执行引擎

## Maintainer Notes

如需扩大执行深度，应以“保持协议稳定、降低首次上手门槛”为优先原则，避免破坏现有文档与配置口径一致性。
