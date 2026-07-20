# Codex 在本机无法自跑（双重环境限制）

Day7 的 Codex 实验侧没能让 Codex CLI 自己跑起来，根因是两层限制叠加，不是代码问题：

1. **OpenAI 账号登录被地区限制**：`codex login --device-auth` 需要 OpenAI 账号，但本机环境注册/登录要求海外手机号验证，连 Google 账号登录也被地区/IP 拦截，无法完成 OAuth。
2. **换 DeepSeek 后端也不兼容**：即使把 `provider.openai.base_url` 指到 `https://api.deepseek.com/v1`，Codex 仍连 `api.openai.com`，自定义 `base_url` 被直接忽略；更根本的是 Codex 依赖 OpenAI 的 **Responses API**（`/v1/responses`），而 DeepSeek 只提供 Chat Completions API（`/v1/chat/completions`），没有 Responses 端点。因此 Codex 的后端换不成 DeepSeek。

处置：按 Codex 文档化纪律（先计划 → 审批 → 改动 → 验证）由操作员代执行同一改动，`agent-lab` 得到与 `agent-lab-2` 完全相同的 `git diff` 与测试结果，对比仍有意义。

提醒：借用的设备上，工具凭据/网络受限是常态，做实验前先 `codex --version`、检查 `OPENAI_API_KEY` 与登录态，别把"装好软件"误当成"配好凭据"。

关联：[[Day7 知识库]] [[Agent 权限与审批]]
