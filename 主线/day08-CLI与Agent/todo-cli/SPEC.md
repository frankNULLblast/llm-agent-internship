# Todo CLI

- `python todo.py add "内容"`：新增未完成事项并返回整数 ID。
- `python todo.py list`：按 ID 显示全部事项。
- `python todo.py done ID`：把存在的事项标记完成。
- `python todo.py delete ID`：删除存在的事项。
- `python todo.py clear-done`：删除所有已完成（done 为 true）的事项，打印删除数量。
- 数据保存到当前目录 `todos.json`，UTF-8。
- 空内容、非整数或不存在的 ID 返回中文错误和非 0 退出码。
- 只使用 Python 标准库。
