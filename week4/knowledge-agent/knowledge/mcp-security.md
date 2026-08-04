# MCP 与安全

MCP 让 Client 使用统一协议发现和调用 Server 提供的 Tools、Resources 与 Prompts。MCP 负责连接规范，不会自动保证工具安全。

提示注入可能诱导 Agent 忽略规则或越权操作。防护应落在权限隔离、工具白名单、参数校验、人工确认和调用上限等程序边界，不能只依赖提示词。
