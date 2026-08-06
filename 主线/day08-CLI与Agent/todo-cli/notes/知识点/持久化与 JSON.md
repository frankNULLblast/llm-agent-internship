# 持久化与 JSON

> 一句话：程序关了数据还在，才叫持久化。

## 本项目怎么持久化
- 数据文件固定为当前目录的 `todos.json`，UTF-8 编码
- 用标准库 `json` + `pathlib.Path` 读写，不引第三方包
- `save()` 写：`json.dumps(items, ensure_ascii=False, indent=2)`，`ensure_ascii=False` 保中文不被转义成 `\uXXXX`
- `load()` 读：文件不存在返回 `[]`；不是 list 抛格式错误；`JSONDecodeError` 被上层捕获，原文件保留供人工恢复

## 验收要点
- 重启新进程后 `list` 仍显示旧数据 → 持久化达标
- 每次改动（add/done/delete）后都 `save()`，否则内存改了磁盘没改，重启就丢

## 常见坑
- 忘了调 `save` → 每次启动数据消失
- 系统默认编码不是 UTF-8 → 中文路径/内容乱码，显式指定 `encoding="utf-8"`
- JSON 损坏 → 捕获 `JSONDecodeError`，别让堆栈直接炸，保留原文件

## 关联
- [[Day8 知识库]]、[[Day8 实习日志 Better than before]]
- 编码细节见 [[知识点/Agent 协作纪律：先计划后实现]]
