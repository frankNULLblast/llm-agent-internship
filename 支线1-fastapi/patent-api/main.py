from collections.abc import Callable
from typing import Literal

from fastapi import Depends, FastAPI, HTTPException
from openai import APIError
from pydantic import BaseModel, ConfigDict, Field

from fee_calc import calculate
from patent_bill import build_result, extract


APP_VERSION = "0.1.0"

app = FastAPI(
    title="专利业务教学 API",
    version=APP_VERSION,
    description="只处理虚构教学数据，不用于真实专利、票据或财务判断。",
)


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class HealthResponse(StrictModel):
    status: Literal["ok"]
    version: str


class FeeRecord(StrictModel):
    patent_application_number: str
    fee_type: str
    amount_yuan: str


class FeeSummary(StrictModel):
    currency: Literal["CNY"]
    record_count: int
    by_application: dict[str, str]
    by_fee_type: dict[str, str]
    total_yuan: str


class PatentBillRecord(StrictModel):
    document_type: str | None
    patent_application_number: str | None
    invoice_number: str | None
    issue_date: str | None
    payer: str | None
    payee: str | None
    service_item: str | None
    amount_yuan: int | float | None
    confidence: int | float


class ReviewResult(StrictModel):
    record: PatentBillRecord
    route: Literal["standard_manual_review", "priority_manual_review"]
    review_reasons: list[str]


class OCRTextRequest(StrictModel):
    ocr_text: str = Field(min_length=1, max_length=8000)


Extractor = Callable[[str], dict]


def get_extractor() -> Extractor:
    return extract


@app.get("/health", response_model=HealthResponse, tags=["system"])
def health() -> HealthResponse:
    return HealthResponse(status="ok", version=APP_VERSION)


@app.post(
    "/api/v1/fees/summary",
    response_model=FeeSummary,
    tags=["fees"],
)
def summarize_fees(records: list[FeeRecord]) -> FeeSummary:
    try:
        result = calculate([record.model_dump() for record in records])
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return FeeSummary.model_validate(result)


@app.post(
    "/api/v1/patent-bills/review",
    response_model=ReviewResult,
    tags=["patent bills"],
)
def review_patent_bill(record: PatentBillRecord) -> ReviewResult:
    try:
        result = build_result(record.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ReviewResult.model_validate(result)


@app.post(
    "/api/v1/patent-bills/recognize",
    response_model=ReviewResult,
    tags=["patent bills"],
)
def recognize_patent_bill(
    request: OCRTextRequest,
    extractor: Extractor = Depends(get_extractor),
) -> ReviewResult:
    try:
        result = build_result(extractor(request.ocr_text))
    except RuntimeError as exc:
        if "DEEPSEEK_API_KEY" in str(exc):
            raise HTTPException(status_code=503, detail="模型服务未配置") from exc
        raise HTTPException(status_code=502, detail="模型服务调用失败") from exc
    except (APIError, ValueError) as exc:
        raise HTTPException(status_code=502, detail="模型服务调用失败") from exc
    return ReviewResult.model_validate(result)
