# Econ-OS 2.0 Activation Notes

本文件用于说明仓库当前已启用的 Econ-OS 2.0 工作流要点，方便维护者快速核对。

## Current Activation State

- 工作流版本：`econ-os-2.0`
- 默认模式：`prompt-only`（无需 API key 即可体验）
- 执行方式：仅当启用 `openai-compatible` 且命令带 `--execute` 时调用模型
- 主入口：CLI `python -m econflow ...` 与本地 Web UI `python -m econflow webui`

## Quick Verification

```bash
python -m econflow --help
python -m econflow status
```

如果需要调用模型：
1. 在 `workflow.toml` 将 `[llm].mode` 改为 `openai-compatible`
2. 配置 `OPENAI_API_KEY`
3. 在 `run` 或 `pipeline` 命令中追加 `--execute`

## Reference Documents

- `README.md`
- `shared-notes/.econ-os/README.md`
- `shared-notes/.econ-os/AGENT_ROLES.md`
- `shared-notes/.econ-os/INTEGRATION_GUIDE.md`
