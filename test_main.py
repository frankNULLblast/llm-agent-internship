import pytest
from fastapi.testclient import TestClient

from main import app


client = TestClient(app)

VALID_FEES = [
    {
        "patent_application_number": "CN202410123456.7",
        "fee_type": "代理服务费",
        "amount_yuan": "3500.00",
    },
    {
        "patent_application_number": "CN202410123456.7",
        "fee_type": "年费",
        "amount_yuan": "900.50",
    },
    {
        "patent_application_number": "CN202410123457.5",
        "fee_type": "代理服务费",
        "amount_yuan": "1200",
    },
]

VALID_BILL = {
    "document_type": "电子发票",
    "patent_application_number": "CN202410123456.7",
    "invoice_number": "24503100000123456789",
    "issue_date": "2026-07-10",
    "payer": "示例智能科技有限公司",
    "payee": "示例知识产权服务有限公司",
    "service_item": "发明专利申请代理服务费",
    "amount_yuan": 3500.0,
    "confidence": 0.95,
}


def test_health_returns_version() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": "0.1.0"}


def test_openapi_contains_business_paths() -> None:
    response = client.get("/openapi.json")

    assert response.status_code == 200
    paths = response.json()["paths"]
    assert "/api/v1/fees/summary" in paths
    assert "/api/v1/patent-bills/review" in paths


def test_fee_summary_is_correct() -> None:
    response = client.post("/api/v1/fees/summary", json=VALID_FEES)

    assert response.status_code == 200
    result = response.json()
    assert result["record_count"] == 3
    assert result["by_application"]["CN202410123456.7"] == "4400.50"
    assert result["by_fee_type"]["代理服务费"] == "4700.00"
    assert result["total_yuan"] == "5600.50"


def test_empty_fee_batch_is_400() -> None:
    response = client.post("/api/v1/fees/summary", json=[])

    assert response.status_code == 400
    assert "非空 JSON 数组" in response.json()["detail"]


def test_missing_fee_field_is_422() -> None:
    record = VALID_FEES[0].copy()
    record.pop("fee_type")

    response = client.post("/api/v1/fees/summary", json=[record])

    assert response.status_code == 422


def test_extra_fee_field_is_422() -> None:
    record = VALID_FEES[0] | {"currency": "CNY"}

    response = client.post("/api/v1/fees/summary", json=[record])

    assert response.status_code == 422


def test_fee_amount_wrong_type_is_422() -> None:
    record = VALID_FEES[0] | {"amount_yuan": 1}

    response = client.post("/api/v1/fees/summary", json=[record])

    assert response.status_code == 422


@pytest.mark.parametrize("amount", ["0", "-1", "abc", "10.001"])
def test_invalid_fee_amount_is_400(amount: str) -> None:
    record = VALID_FEES[0] | {"amount_yuan": amount}

    response = client.post("/api/v1/fees/summary", json=[record])

    assert response.status_code == 400


def test_bad_fee_patent_number_is_400() -> None:
    record = VALID_FEES[0] | {"patent_application_number": "unknown"}

    response = client.post("/api/v1/fees/summary", json=[record])

    assert response.status_code == 400


def test_complete_bill_uses_standard_manual_review() -> None:
    response = client.post("/api/v1/patent-bills/review", json=VALID_BILL)

    assert response.status_code == 200
    result = response.json()
    assert result["route"] == "standard_manual_review"
    assert result["review_reasons"] == []


def test_low_confidence_uses_priority_manual_review() -> None:
    record = VALID_BILL | {"confidence": 0.5}

    response = client.post("/api/v1/patent-bills/review", json=record)

    assert response.status_code == 200
    assert response.json()["route"] == "priority_manual_review"
    assert "模型置信度低于 0.85" in response.json()["review_reasons"]


def test_null_amount_uses_priority_manual_review() -> None:
    record = VALID_BILL | {"amount_yuan": None}

    response = client.post("/api/v1/patent-bills/review", json=record)

    assert response.status_code == 200
    assert "缺少金额" in response.json()["review_reasons"]


def test_bad_bill_patent_number_uses_priority_manual_review() -> None:
    record = VALID_BILL | {"patent_application_number": "unknown"}

    response = client.post("/api/v1/patent-bills/review", json=record)

    assert response.status_code == 200
    assert response.json()["route"] == "priority_manual_review"


def test_extra_bill_field_is_422() -> None:
    record = VALID_BILL | {"approved": True}

    response = client.post("/api/v1/patent-bills/review", json=record)

    assert response.status_code == 422
