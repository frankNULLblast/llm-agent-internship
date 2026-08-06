# 本地发布检查表

- 版本或 Git 提交：day11 首个提交（md_stats.py + 测试 + 样例 + 本文档）
- 需求与非目标：递归扫描目录下 `.md` 文件，按不区分大小写统计关键词出现次数；忽略 `.git` 和 `.venv`；输出每文件计数及总计；目录或关键词无效时非 0 退出。非目标：不引入数据库、不做网络请求、不统计非 `.md` 文件。
- 数据流/文件设计：目录 → `rglob("*.md")` 过滤 IGNORED → 逐文件 `re.escape(keyword)` 字面量、忽略大小写计数 → 打印每文件计数与 TOTAL。
- 集成入口：`python md_stats.py samples agent`
- 测试命令与实际结果：`python -m unittest -v` → `Ran 3 tests ... OK`
- 全新终端复现结果：`python md_stats.py samples agent` 输出 `a.md  3` / `b.md  1` / `TOTAL  4`；`python md_stats.py missing agent` 退出码 1。
- 已知限制：关键词只做字面量匹配（`.` `+` 等按普通字符处理，符合需求）；不统计二进制或非 UTF-8 文件（跳过并报告）。
- 回退方法：切回上一个可运行 Git 提交（`git checkout <sha>`）。
