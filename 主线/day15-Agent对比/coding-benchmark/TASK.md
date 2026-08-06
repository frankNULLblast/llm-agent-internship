# 对比测试题：可插拔文档分块框架 `minichunk`

> 用法：把下面「题面」整段原文复制给被测模型，**不要补充任何说明、不要分段提问**。
> 两个模型收到的字符必须完全一致，这是对比成立的前提。

---

## 题面（复制这一段）

请实现一个名为 `minichunk` 的 Python 包，用于把长文档切分成检索友好的块（chunk）。这是一个**框架**，不是一次性脚本：第三方要能在不修改你源码的前提下接入自己的切分策略。

### 环境约束

- Python 3.10+
- **只允许标准库**，不得引入任何第三方依赖
- 代码需能在 Windows 与 Linux 上一致运行

### 必须实现的公开 API（名称与签名不得更改）

```python
from minichunk import Chunk, get_chunker, register

chunker = get_chunker("fixed", chunk_size=100, overlap=20)
chunks = chunker.split(text)          # -> list[Chunk]

c = chunks[0]
c.text     # str，该块的文本
c.start    # int，在原文中的起始下标
c.end      # int，在原文中的结束下标（不含）
c.meta     # dict，策略相关的附加信息
```

### 内置策略（三种，通过 `get_chunker(name, ...)` 取用）

1. `"fixed"` — 定长切分，参数 `chunk_size: int`、`overlap: int = 0`。相邻块之间需有 `overlap` 个字符的重叠。
2. `"sentence"` — 按句子边界切分，需同时正确处理中文标点（`。！？；`）与英文标点（`. ! ?`），支持中英混排。参数 `max_chars: int`，允许把连续短句合并进同一块，但合并后不得超过 `max_chars`。
3. `"markdown"` — 按 Markdown 标题层级切分。每个块的 `meta` 中必须包含键 `heading_path`，其值为从一级标题到当前标题的路径列表，例如 `["安装", "Windows"]`。正文不属于任何标题时 `heading_path` 为 `[]`。

### 硬性契约

1. **偏移可回切**：对任意策略、任意输入，必须满足 `original_text[c.start:c.end] == c.text`。
2. **参数校验**：`chunk_size <= 0` 或 `overlap >= chunk_size` 或 `overlap < 0` 时，抛出 `ValueError`。
3. **空输入**：`split("")` 返回空列表 `[]`，不得抛异常。
4. **插件注册**：提供装饰器 `register(name)`，第三方写如下代码即可让 `get_chunker("mine")` 生效，且**不需要改动 `minichunk` 包内任何文件**：

   ```python
   from minichunk import register

   @register("mine")
   class MyChunker:
       def __init__(self, **kwargs): ...
       def split(self, text: str) -> list: ...
   ```

5. **未知策略**：`get_chunker("not_exist")` 抛出 `KeyError` 或 `ValueError`。
6. **命令行入口**：支持

   ```
   python -m minichunk --strategy fixed --file <路径> --chunk-size 100 --overlap 20 --json
   ```

   `--json` 时向标准输出打印合法 JSON 数组，每个元素含 `text` / `start` / `end` / `meta` 四个键。

### 交付要求

- 给出完整目录结构与每个文件的完整代码，标明文件路径。
- 自带测试（`pytest` 风格或标准库 `unittest` 均可，但测试本身不得依赖第三方库）。
- 附一段简短说明：如果要新增第四种策略，需要改动哪些地方。

---

## 出题说明（不要发给模型）

这道题的区分度来自四个埋点，按被踩概率从高到低：

| 埋点 | 为什么能拉开差距 |
|---|---|
| **偏移可回切**（契约 1） | 大量实现会顺手 `strip()` 或做空白归一化，一旦如此 `text[start:end] != c.text`，检索时引用定位就全错。这是最能区分「写得能跑」和「写得对」的一条。 |
| **插件注册不改源码**（契约 4） | 只有真正用了注册表 + 装饰器的实现才过。用 `if name == "fixed": ...` 硬编码工厂的写法，功能上能跑，但新增策略必须改框架源码，架构分直接掉。 |
| **markdown 的 heading_path** | 要维护标题层级栈（h2 出现时弹出更深层级），只记「最近一个标题」是最常见的偷懒解法。 |
| **中英混排句子切分** | 容易只处理中文句号，或用 `split(".")` 把小数、缩写切碎。 |

另外这道题选它还有三个现实理由：纯本地、零 API key、零网络依赖，所以两边环境完全对等；题量一次会话能做完；而且它就是你 Day18 文档切分那套东西的框架化版本，你懂业务，能判断谁写得好。
