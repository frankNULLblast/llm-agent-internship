# 教材 Day 8 的 ops/init_checkpoints.py（需合并进工程）。
#
# ⚠️ 可运行代码位置说明：
#   当天真实跑通的代码在培训 VM 的 patent-agent-service（Day 3 提交 e13000b 之上的演进）。
#   本仓库仅保留教材对应的设计与配置，未含 VM 实跑代码与输出。

import os

from langgraph.checkpoint.postgres import PostgresSaver


def main() -> int:
    url = os.getenv("LANGGRAPH_DATABASE_URL")
    if not url:
        raise RuntimeError("未设置 LANGGRAPH_DATABASE_URL")
    # 只初始化 LangGraph 内部 checkpoint 表；应用表由 Alembic 管理。
    # setup() 可重复执行，便于新克隆初始化。
    with PostgresSaver.from_conn_string(url) as checkpointer:
        checkpointer.setup()
    print("LangGraph checkpoint schema: ready")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
