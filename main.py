import sys
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict

# 复用 Day 6 的费用汇总逻辑（业务规则只留一份，不复制）：把 fee_calc.py 所在目录加入导入路径
FEE_CALC_DIR = Path(__file__).resolve().parent.parent.parent / "software-process" / "day06" / "fee-calculator"
sys.path.insert(0, str(FEE_CALC_DIR))
from fee_calc import calculate  # noqa: E402


APP_VERSION = "0.1.0"

app = FastAPI(
    title="专利业务教学 API",
    summary="专利业务教学 API 的最小可用版本，仅用于实习演示。",
    version=APP_VERSION,
    description="只处理虚构教学数据，不用于真实专利、票据或财务判断。",
    contact={"name": "实习教学助手", "email": "student@example.com"},
)


class HealthResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    status: Literal["ok"]
    version: str


@app.get("/health", response_model=HealthResponse, tags=["system"])
def health() -> HealthResponse:
    return HealthResponse(status="ok", version=APP_VERSION)


# ---- Day 2：把 Day 6 的费用汇总逻辑包成 HTTP 接口 ----

class FeeRecord(BaseModel):
    """单条费用记录，字段与 Day 6 的 fee_calc.calculate 完全一致。"""

    patent_application_number: str
    fee_type: str
    amount_yuan: str  # 保持字符串，直接交给 calculate 的 parse_amount 校验


class FeeSummaryRequest(BaseModel):
    """请求体：费用记录数组。"""

    records: list[FeeRecord]


class FeeSummaryResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    currency: str
    record_count: int
    by_application: dict[str, str]
    by_fee_type: dict[str, str]
    total_yuan: str


@app.post("/api/v1/fees/summary", response_model=FeeSummaryResponse, tags=["fees"])
def summarize_fees(request: FeeSummaryRequest) -> FeeSummaryResponse:
    try:
        result = calculate([record.model_dump() for record in request.records])
    except ValueError as exc:
        # calculate 的校验失败属于"请求不符合业务规则"，映射成 422
        raise HTTPException(status_code=422, detail=str(exc))
    return FeeSummaryResponse(**result)
