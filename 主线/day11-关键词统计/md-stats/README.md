# Markdown 关键词统计器（md_stats）

递归扫描目录下所有 `.md` 文件，按**不区分大小写、按字面量**统计关键词出现次数，忽略 `.git` 与 `.venv`，并打印每文件计数与总计。仅使用 Python 标准库。

## 安装

需要 Python 3.10+。无需第三方依赖。

```powershell
# Windows（使用统一 venv 或系统 python 均可）
cd week2\day11\md-stats
python md_stats.py samples agent
```

```bash
# Linux / macOS
cd week2/day11/md-stats
python md_stats.py samples agent
```

## 用法

```text
python md_stats.py <目录> <关键词>
```

- `<目录>`：要扫描的根目录（不存在则退出码 1）。
- `<关键词>`：要统计的词，按字面量匹配（正则特殊字符 `.` `+` `*` 等不当作通配符），不区分大小写。

示例：

```text
python md_stats.py samples agent
a.md    3
b.md    1
TOTAL   4
```

```text
python md_stats.py missing agent
错误：目录不存在
（退出码 1）
```

## 测试

```text
python -m unittest -v
```

预期：`Ran 3 tests ... OK`

## 目录结构

```text
md-stats/
├── md_stats.py            # 主程序
├── test_md_stats.py       # 单元测试
├── RELEASE_CHECKLIST.md   # 本地发布检查表
├── samples/
│   ├── a.md
│   └── b.md
└── README.md
```

## 六阶段

需求 → 设计（目录扫描—过滤—计数—输出）→ 编码（md_stats.py）→ 集成（samples → CLI 输出）→ 测试（test_md_stats.py + 退出码）→ 上线（全新终端按本文档运行）。
