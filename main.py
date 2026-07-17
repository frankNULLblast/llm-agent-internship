from typing import Literal

from fastapi import FastAPI
from pydantic import BaseModel, ConfigDict


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
