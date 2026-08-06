# 把 CLI 计算逻辑包成 API

Day 6 的 `fee_calc.calculate(records)` 是个纯函数：吃一个记录列表，吐一个汇总 dict，不碰文件、不碰 argparse、不碰标准输入。这种函数最适合直接搬进 Web 服务当"算账内核"。

## 复用，不复制

`patent-api` 和 `day06/fee-calculator` 是兄弟目录。我在 `main.py` 里把 `fee_calc.py` 所在目录加进 `sys.path`，然后 `from fee_calc import calculate`：

```python
FEE_CALC_DIR = Path(__file__).resolve().parent.parent.parent / "software-process" / "day06" / "fee-calculator"
sys.path.insert(0, str(FEE_CALC_DIR))
from fee_calc import calculate
```

这样 `calculate` 只有一份源码（在 Day 6 项目里），Web 服务只是调用它。Day 1 笔记就强调过"业务规则只留一份"，这里落到了实处：哪天改费率规则，只改 `fee_calc.py` 一处，API 自动跟着变。

## HTTP 是无状态的，每次整批交

CLI 版可以从文件读一大批记录慢慢算；HTTP 版每次请求自带全部 `records`，算完返回，不存中间状态。所以端点设计成 `POST /api/v1/fees/summary`，请求体就是整个记录数组，响应就是这次的汇总。没有"上一次传了一半"这回事。

## 校验失败怎么变成 422

`calculate` 自己会抛 `ValueError`（申请号格式错、金额不合法、记录为空等）。在 API 里我把它接住、转成 HTTP 状态码：

```python
try:
    result = calculate([r.model_dump() for r in request.records])
except ValueError as exc:
    raise HTTPException(status_code=422, detail=str(exc))
```

`422` 和"请求体不符合 Pydantic Schema"是同一类语义——都是"你给我的数据不对"，客户端好理解。

## 测试还是用 TestClient

和 Day 1 一样，`test_main.py` 里用 `TestClient` 在当前进程内发 `POST`，不启真端口。新增三个用例：正常汇总返回 200 且字段对、非法申请号返回 422、空数组返回 422。`pytest` 跑出 `4 passed`。

关联
- [[Day2 知识库]]
- [[请求模型与 POST 请求体]]
- [[Day1 知识库]]
