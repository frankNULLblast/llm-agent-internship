# Day 4 每日总结

日期：2026-07-15（星期三）

## 今日完成
- 完成 Day 4「第一次 API 调用与结构化输出」。
- 在 `.venv` 中确认 `openai` 已安装（2.45.0），三个环境变量 `DEEPSEEK_API_KEY / DEEPSEEK_BASE_URL / DEEPSEEK_MODEL` 均已就位（实际模型为 `deepseek-v1-tflash`）。
- 写出两个脚本并放仓库 `week1/day04/`：
  - `chat_once.py`：单轮问答，读环境变量建客户端，捕获四类异常并打印 Token 用量。
  - `extract_json.py`：用 `response_format=json_object` 抽取 `{name, course, score}`，做字段/类型校验。
- 挑战任务 `log_usage.py`：成功调用后把 Token 用量追加到 `usage.jsonl`（不含提示词、不含密钥）。

## 验证结果（诚实记录）
- ✅ 无参数运行 `chat_once.py` → 显示用法、退出码 **2**（不调 API）。
- ✅ 临时移除 Key 运行 → 中文提示「未设置 DEEPSEEK_API_KEY」、退出码 **6**（无堆栈）。
- ✅ 真实调用（2026-07-17，Key 充值后）全部成功：单轮问答返回回答+用量、两次 JSON 抽取分别得 `score:92` 与 `score:null`、`usage.jsonl` 写入首行真实用量（见下方「真实运行结果」）。
  - 注：环境预设 `DEEPSEEK_MODEL=deepseek-v1-tflash` 在官方 `api.deepseek.com` 不被接受（报 400），运行时改用官方模型 `deepseek-chat` 跑通。后续 day5/day6 建议同样将 `DEEPSEEK_MODEL` 改为 `deepseek-chat` 或 `deepseek-v4-flash`。

## 三个我现在能讲清楚的概念
1. **SDK 本质还是 HTTPS**：`openai` 包只是帮你拼请求、发 HTTPS、解析响应；以前是浏览器替你发，今天起是 Python 自己发。
2. **四类异常对应不同故障层**：认证失败(3)/网络断了(4)/服务返回错误如 400/402(5)/本机没设 Key(6)；每个都有独立中文提示与退出码，方便定位。
3. **密钥绝不进代码**：Key 只从环境变量读，`.py` 文件、Git、截图里都不出现。

## 卡住的点与处理
- **DeepSeek Key 余额不足（402）** → 已解决：用户充值后 402 消失，真实调用跑通。
- **模型名不匹配（400）**：环境预设 `deepseek-v1-tflash` 官方 endpoint 不支持，运行时用 `deepseek-chat` 跑通（详见下方真实运行结果备注）。
- **教程 `extract_json.py` 漏了 API 错误捕获**（原版只捕获 JSON 解析异常，遇 402/400 会抛堆栈、退出码 1）。已按 Day 4「安全处理常见异常」的意图，补上与 `chat_once.py` 一致的异常捕获，现退出码 5 且中文提示。

## 每日总结要记的两笔（验收清单补充）
- 一次成功调用的 Token 用量：`usage.jsonl` 首行 `{model:deepseek-chat, prompt_tokens:18, completion_tokens:24, total_tokens:42}`。
- 一次故障演练的退出码：**6**（缺 Key），**5**（402/400 余额或模型错误）。

## 明日计划
- Day 4 真实调用已全部跑通，验收清单 5 条达成；下一步进入 Day 5：专利票据识别 Demo（写 `patent_bill.py` + 离线 `unittest`），这是 FastAPI 加餐的前置。

## 真实运行结果（2026-07-17，Key 已充值，模型 deepseek-chat）
- [x] `chat_once.py "用一句话解释什么是 Token"` → 真实回答：「Token是AI模型处理文本时使用的最小单位，可以是一个词、一个字或一段字符。」+ `[usage] input=18 output=20 total=38`
- [x] `extract_json.py "学生林明..."` → `{"name":"林明","course":"Python程序设计","score":92}` ✅
- [x] `extract_json.py "学生周雨..."` → `{"name":"周雨","course":"数据结构","score":null}` ✅
- [x] `log_usage.py` 成功一次 → `usage.jsonl` 首行：`{"timestamp":"2026-07-17T01:37:35Z","model":"deepseek-chat","prompt_tokens":18,"completion_tokens":24,"total_tokens":42}`
## 成果附件

![[564b4ee76f6670a1324f84a55562c181.png]]
![[5fdc25a90f1b2523b760e31e3277a445.png]]
![[c58bc2a7aab0c87de6cc3ad345e075b9.png]]
密钥安全管理：环境变量而非硬编码

> 原子笔记 · 关联：[[API 调用的四类异常与退出码]] ｜ [[用 SDK 发请求本质还是 HTTPS]]

铁律
**API Key 相当于服务账号的秘密通行证，绝不能写进 `.py` 文件。**

Day 4 的做法：Key 只从环境变量读——

```python
api_key = os.getenv("DEEPSEEK_API_KEY")
if not api_key:
    raise RuntimeError("未设置 DEEPSEEK_API_KEY，请先按教程安全输入。")
```

`base_url`、`model` 也用 `os.getenv(..., 默认值)` 读取，既灵活又不硬编码。

为什么
- 写进 `.py` → 一 `git commit` / 一截图就泄露，且极难彻底撤回（Key 进了 git 历史就永久可见）。
- 放环境变量 → 代码可安全提交、可贴群、可演示，Key 留在你机器/会话里。

配套纪律
- 设置方式：教程 §2.4 的「安全设置 DeepSeek API Key」——临时 `set`/`export`，或写进 shell 配置文件（仍不进仓库）。
- 验收清单明写：「Key 不在代码、Git 或截图中」。
- 本机实测 `DEEPSEEK_MODEL` 实际值是 `deepseek-v1-tflash`（非教程默认 v4-flash），脚本用 `os.getenv` 自动取环境值，无需改代码。

 还机前提醒（长期约定）
这台电脑是借用的，PAT/Key 这类凭证在归还前需吊销并清理 Windows 凭据，避免随机器留下。
用 SDK 发请求本质还是 HTTPS

> 原子笔记 · 关联：[[API 调用的四类异常与退出码]] ｜ [[密钥安全管理：环境变量而非硬编码]]

核心
`openai` 这个 SDK 包**不是魔法**，它最终仍通过 **HTTPS 请求**远程服务。`chat.completions.create(...)` 等价于：你的 Python 拼好一个 JSON 请求体，用 `POST` 发到 `https://api.deepseek.com/chat/completions`，再把返回的 JSON 解析成对象。

 为什么这事重要
- 之前在浏览器聊天，是**网页替你发请求**（带着你的登录态）。
- 本日（Day 4）起，是 **Python 自己发请求**（带着你的 API Key）。
- 所以「网络/密钥/限流/格式」这些浏览器帮你兜住的事，现在**你要自己处理**——这正是 [[API 调用的四类异常与退出码]] 存在的理由。

一句话
SDK = 帮你拼请求、发 HTTPS、解析响应的工具；模型在远端，不在你电脑里。这也呼应 Day 3 的 [[网页产品能力 ≠ 底层模型能力]]：你调的是同一个底层模型，只是入口从网页变成了代码。
API 调用的四类异常与退出码

> 原子笔记 · 关联：[[用 SDK 发请求本质还是 HTTPS]] ｜ [[密钥安全管理：环境变量而非硬编码]]

Day 4 的两个脚本都捕获了四类异常，各自给中文提示 + 非零退出码，方便定位是哪一层炸了。

四类异常对照

| 异常 | 含义 | 哪层出问题 | chat_once 退出码 | extract_json 退出码 |
|---|---|---|---|---|
| `AuthenticationError` | 认证失败（Key 错/无效） | 凭证层 | 3 | 3 |
| `APIConnectionError` | 网络连接失败 | 网络层 | 4 | 4 |
| `APIStatusError` | 服务返回错误状态码 | 服务层（如 401/402/429/500） | 5 | 5 |
| `RuntimeError`（本机未设 Key） | 环境变量缺失 | 本机配置层 | 6 | 2（缺 Key 直接 return 2） |

> 注：`APIStatusError` 携带 `exc.status_code`，可打印出具体 HTTP 码（如本日实测 **402 余额不足**）。

为什么这么设计
- 每个异常**独立提示 + 独立退出码**，用户/你一眼知道该去查 Key、查网络、还是查余额。
- 最关键的一条纪律：**绝不让 Python 堆栈直接对用户**。`except` 兜住后打印人话，程序以非 0 退出，这才算「安全处理常见异常」（Day 4 今日成果原话）。

本日实测
- 缺 Key → 退出码 **6**（chat_once）/ **2**（extract_json 缺 Key 分支），中文提示「未设置 DEEPSEEK_API_KEY」。
- 402 余额不足 → 退出码 **5**，`API 返回错误：HTTP 402`。
- 未捕获时（教程原版 extract_json 漏了 API 错误分支）会抛完整堆栈、退出码 1——已修复。

延伸（和 Day 3 状态码对照）
HTTP 状态码的归属思路和 Day 3 的 422/400/200/500 一脉相承：**先分清是「形状错」「值错」还是「程序崩了」**，再到对应层去修。
response_format 与 JSON 校验

> 原子笔记 · 关联：[[system 与 user 消息的分工]] ｜ [[API 调用的四类异常与退出码]]

目标
让模型输出**机器能直接用的结构化数据**，而不是一段人读的文字。Day 4 的 `extract_json.py` 从一句话里抽 `{name, course, score}`。

两层保险
1. **请求侧逼模型吐 JSON**：`response_format={"type": "json_object"}` 要求返回合法 JSON 对象；再在 system 里写清「字段为 name/course/score，score 必须是整数，未知用 null」。
2. **响应侧自己校验**（不能全信模型）：
   - `json.loads(content)` 解析，失败 → 退出码 3（不是有效 JSON）。
   - 检查 `type(data) is dict`、字段集合恰好是 `{name, course, score}`、`score` 是 int 或 None，不符 → 退出码 4。

```python
required = {"name", "course", "score"}
if type(data) is not dict or set(data) != required or type(data["score"]) not in (int, type(None)):
    print(f"JSON 字段或类型不符合约定：{data}", file=sys.stderr)
    return 4
```

为什么必须自己校验
- `response_format` 提高吐 JSON 的概率，但**不保证字段/类型一定对**（模型可能多字段、把 score 写成字符串）。
- 程序侧校验是「确定性规则」，比模型抽查可靠——这正是 Day 5/Day 6「模型负责抽取、程序负责校验」思想的预演，也呼应 FastAPI 加餐里「业务规则只存在一处」。

 空内容兜底
模型偶发返回空 `content` → 提示「模型返回空内容，请重试」，不写无限重试循环（教程常见错误表明确写法）。
system 与 user 消息的分工

> 原子笔记 · 关联：[[用 SDK 发请求本质还是 HTTPS]] ｜ [[response_format 与 JSON 校验]]

核心
`messages` 是一个角色列表，两种常用角色：
- **`system`**：定义**长期规则 / 人设 / 约束**，对整段对话一直生效。例：「简洁回答；不知道时明确说不知道。」
- **`user`**：提供**本次具体任务 / 输入**。例：「用一句话解释什么是 Token」。

为什么分开
- system 放「永恒约束」，user 放「这一次要什么」——改任务时只动 user，不动 system。
- 模型按 system 定的调性来组织 user 给的内容。比如 system 说「只输出 JSON 对象」，user 给一句话，模型就会吐 JSON 而不是散文。

实践要点
- system 越明确，输出越可控。Day 4 的 `extract_json.py` 就是把「只输出 JSON、字段为 name/course/score、未知用 null」写进 system，再配合 [[response_format 与 JSON 校验]] 双保险。
- 不要为了「更聪明」把长篇背景塞进 user 还指望模型记住——该进 system 的规则就进 system。
