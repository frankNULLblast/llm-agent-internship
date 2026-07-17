# 本地发布检查表

- 版本：v0.1.0
- 需求与非目标已核对：是（REQUIREMENTS.md 已包含用户、输入、输出、错误、非目标、固定验收）
- `python -m unittest -v` 实际结果：`Ran 9 tests ... OK`（9 个固定测试全部通过）
- 固定输入总额：`5600.50`（与 REQUIREMENTS.md 固定验收一致）
- README 命令已在预发布克隆目录复现：是（从 `fee-calculator-release-check` 克隆目录运行 `python -m unittest -v` 与 `python fee_calc.py fees.json -o summary.json`，9 测试 OK、总额 5600.50 复现）
- 已知限制已记录：是（README 已知限制 + 业务边界说明）
- 输出不含真实数据或密钥：是（fees.json 为虚构教学样例，代码中无 Key）
- 回退方法：停止使用当前目录，重新从上一已知可运行提交建立新目录；不在原目录执行破坏性回退。
