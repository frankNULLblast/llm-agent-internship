# Todo CLI

## 环境
Python 3.11，无第三方依赖。

## 使用（Windows/Linux 共用）
```console
python todo.py add "阅读文档"
python todo.py list
python todo.py done 1
python todo.py delete 1
```

## 测试（Windows/Linux 共用）
```console
python -m unittest -v
```

## 数据
数据保存在运行目录的 `todos.json`。不要并发运行多个写入命令。

## 已知限制
没有并发写保护；删除最大 ID 后，该 ID 可能再次使用。
