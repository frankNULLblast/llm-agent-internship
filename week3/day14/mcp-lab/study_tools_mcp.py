"""Day 14: 只读学习资料 MCP Server.

暴露一个 Tool (search_notes) 和两个 Resource (note_index / get_note)。
STDIO 传输：Server 不向 stdout 写任何调试信息，日志走 stderr。
"""

import sys
from pathlib import Path

from mcp.server.fastmcp import FastMCP

ROOT = Path(__file__).with_name("notes").resolve()
mcp = FastMCP("study-tools")


@mcp.tool()
def search_notes(keyword: str) -> str:
    """在授权的 TXT 学习资料中按关键词只读检索。"""
    keyword = keyword.strip()
    if not keyword or len(keyword) > 50:
        return "错误：关键词为空或过长"
    matches = []
    for path in sorted(ROOT.glob("*.txt")):
        text = path.read_text(encoding="utf-8")
        if keyword.casefold() in text.casefold():
            matches.append(f"{path.name}: {text.strip()}")
    return "\n".join(matches) if matches else "未找到匹配笔记"


@mcp.resource("study://index")
def note_index() -> str:
    """返回可用学习资料文件名。"""
    return "\n".join(path.name for path in sorted(ROOT.glob("*.txt")))


# ── 挑战任务：study://note/{name} ──────────────────────────
# 拒绝包含 / \ .. 的文件名，防止路径穿越。
@mcp.resource("study://note/{name}")
def get_note(name: str) -> str:
    """按文件名读取单篇笔记，拒绝路径穿越。"""
    # 第一道防线：字符级校验
    if "/" in name or "\\" in name or ".." in name:
        return "错误：文件名包含非法字符（/ \\ ..）"
    # 只允许 .txt 后缀
    if not name.endswith(".txt"):
        return "错误：只支持 TXT 文件"
    # 第二道防线：resolve 后确认路径仍在 ROOT 下
    path = (ROOT / name).resolve()
    try:
        path.relative_to(ROOT)
    except ValueError:
        return "错误：路径越界"
    if not path.exists():
        return "错误：文件不存在"
    return path.read_text(encoding="utf-8")


if __name__ == "__main__":
    mcp.run(transport="stdio")
