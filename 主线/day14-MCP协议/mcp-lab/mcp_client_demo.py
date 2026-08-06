"""MCP Client: 连接 study_tools MCP Server，展示完整的工具/资源交互。"""

import asyncio
import sys
import os

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

SERVER_SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "study_tools_mcp.py")
PYTHON = sys.executable


async def main():
    server_params = StdioServerParameters(
        command=PYTHON,
        args=[SERVER_SCRIPT],
    )

    print("=" * 60)
    print("  MCP Client -> study-tools Server")
    print("=" * 60)

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            # 1. 初始化握手
            await session.initialize()
            print("\n[握手] initialize OK\n")

            # 2. 列出工具
            print("-" * 60)
            print("  [1] 列出工具 (tools/list)")
            print("-" * 60)
            tools_result = await session.list_tools()
            for tool in tools_result.tools:
                print(f"  名称: {tool.name}")
                print(f"  描述: {tool.description}")
                schema = tool.inputSchema
                props = schema.get("properties", {})
                required = schema.get("required", [])
                for prop_name, prop_info in props.items():
                    req_mark = "*" if prop_name in required else " "
                    print(f"  参数: {req_mark} {prop_name} ({prop_info.get('type', '?')}) - {prop_info.get('description', '')}")
                print()

            # 3. 列出资源
            print("-" * 60)
            print("  [2] 列出资源 (resources/list)")
            print("-" * 60)
            resources_result = await session.list_resources()
            for res in resources_result.resources:
                print(f"  URI:  {res.uri}")
                print(f"  名称: {res.name}")
                print(f"  描述: {res.description}")
                print(f"  MIME: {res.mimeType}")
                print()

            # 4. 调用 search_notes 工具
            test_cases = [
                ("MCP", "正常搜索"),
                ("agent", "正常搜索"),
                ("量子芯片", "无匹配"),
                ("", "空关键词"),
                ("x" * 51, "超长关键词"),
            ]

            for keyword, desc in test_cases:
                print("-" * 60)
                display_kw = keyword if len(keyword) <= 30 else keyword[:30] + "..."
                print(f"  [3] 调用工具 search_notes(keyword=\"{display_kw}\")")
                print(f"      场景: {desc}")
                print("-" * 60)
                result = await session.call_tool("search_notes", {"keyword": keyword})
                for content in result.content:
                    print(f"  结果: {content.text}")
                print()

            # 5. 读取资源 study://index
            print("-" * 60)
            print("  [4] 读取资源 study://index")
            print("-" * 60)
            index_result = await session.read_resource("study://index")
            for content in index_result.contents:
                print(f"  结果: {content.text}")
            print()

            # 6. 读取资源 study://note/mcp.txt
            print("-" * 60)
            print("  [5] 读取资源 study://note/mcp.txt")
            print("-" * 60)
            note_result = await session.read_resource("study://note/mcp.txt")
            for content in note_result.contents:
                print(f"  结果: {content.text}")
            print()

            # 7. 路径穿越攻击测试
            attack_cases = [
                ("../../etc/passwd", "路径穿越 ../../etc/passwd"),
                ("subdir/evil.txt", "子目录 subdir/evil.txt"),
                ("mcp.py", "非 .txt 文件"),
                ("nope.txt", "不存在的文件"),
            ]

            from mcp.shared.exceptions import McpError

            for name, desc in attack_cases:
                print("-" * 60)
                print(f"  [6] 读取资源 study://note/{name}")
                print(f"      场景: {desc}")
                print("-" * 60)
                try:
                    attack_result = await session.read_resource(f"study://note/{name}")
                    for content in attack_result.contents:
                        print(f"  结果: {content.text}")
                except McpError as e:
                    print(f"  拦截: {e}")
                    print(f"  (MCP 框架在 URI 层就拒绝了，未到达 Server 的 get_note)")
                except Exception as e:
                    print(f"  拦截: {type(e).__name__}: {e}")
                print()

            print("=" * 60)
            print("  所有交互完成，MCP Server 工作正常！")
            print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
