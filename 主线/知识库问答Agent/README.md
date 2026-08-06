# Knowledge Agent

本地知识库问答 Agent。它使用标准库关键词检索、DeepSeek OpenAI 兼容 API、来源展示和受控计算器。

## 环境

- Windows + PowerShell 7，或 Linux + Bash
- Python 3.11
- 依赖：`openai`

以下安装、运行和测试命令都在本项目根目录执行。

## 安装（Windows PowerShell）

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install openai
```

## 安装（Linux Bash）

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install openai
```

## 安全设置 API Key（Windows PowerShell）

```powershell
$secureKey = Read-Host "请输入 DeepSeek API Key" -AsSecureString
$env:DEEPSEEK_API_KEY = [System.Net.NetworkCredential]::new('', $secureKey).Password
$env:DEEPSEEK_BASE_URL = 'https://api.deepseek.com'
$env:DEEPSEEK_MODEL = 'deepseek-v4-flash'
```

## 安全设置 API Key（Linux Bash）

```bash
read -rsp "请输入 DeepSeek API Key: " DEEPSEEK_API_KEY
echo
export DEEPSEEK_API_KEY
export DEEPSEEK_BASE_URL='https://api.deepseek.com'
export DEEPSEEK_MODEL='deepseek-v4-flash'
```

## 使用（Windows/Linux 共用）

```console
python agent.py "Token 是什么？"
python agent.py "食堂今天供应什么菜？"
python agent.py "请计算 (12+8)/4"
```

## 测试与评测（Windows/Linux 共用）

```console
python -m unittest discover -v
python eval.py test_questions.json
```

评测中只要有一题未通过，`eval.py` 会返回退出码 `1`，但仍会写出完整报告；这表示存在待分析用例，不表示脚本崩溃。脱敏后的优化前后指标见 `EVAL_SUMMARY.md`，演示顺序见 `DEMO.md`。

## 数据

只读取 `knowledge/` 中 UTF-8 Markdown/TXT。回答后显示程序实际检索到的来源。

## 安全边界

- 无检索结果时在 API 调用前拒答。
- 计算器只支持数字、括号和 `+ - * /`。
- 工具白名单、参数校验、最多 3 轮和最多 3 次工具调用。
- 日志不保存 API Key 和完整用户问题。

## 已知限制

- 关键词检索不理解所有同义表达。
- 自动关键词评分不能替代人工事实核查。
- 仅适用于小型本地资料，不支持并发和生产部署。
- 不具备联网搜索、长期记忆和多用户权限。
