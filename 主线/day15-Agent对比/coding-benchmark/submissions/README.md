# submissions/ — 被测模型的输出放这里

两边都在**全新对话**里只贴 `../TASK.md` 的题面（不要带任何上下文），把拿到的代码原样落盘：

```
submissions/
├── workbuddy/      ← 新开的 WorkBuddy 对话的输出
│   └── minichunk/
│       ├── __init__.py
│       ├── strategies.py
│       └── __main__.py
└── kimi-k3/        ← Kimi K3 新对话的输出
    └── minichunk/
        └── ...（结构以它给的为准，但必须有 minichunk 包目录）
```

注意：

- 目录名随意，但验收脚本要求**提交目录下直接含 `minichunk/` 包**（即 `python verify_chunker.py submissions/workbuddy` 时，里面要有 `minichunk/__init__.py`）。
- 模型给的代码若带 markdown 围栏，去掉围栏只留纯代码。
- 不要替它修任何 bug 再落盘——修了就失去对比意义。

跑分：

```bash
cd ..
python verify_chunker.py submissions/workbuddy --label WorkBuddy --out result_workbuddy.json
python verify_chunker.py submissions/kimi-k3   --label Kimi-K3   --out result_kimi.json
```
