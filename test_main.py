from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


def test_health_returns_version() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": "0.1.0"}


def test_summarize_fees_returns_summary() -> None:
    payload = {
        "records": [
            {"patent_application_number": "CN202310000001.1", "fee_type": "申请费", "amount_yuan": "100.00"},
            {"patent_application_number": "CN202310000001.1", "fee_type": "年费", "amount_yuan": "50.00"},
            {"patent_application_number": "CN202310000002.2", "fee_type": "申请费", "amount_yuan": "200.00"},
        ]
    }
    response = client.post("/api/v1/fees/summary", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["currency"] == "CNY"
    assert data["record_count"] == 3
    assert data["total_yuan"] == "350.00"
    assert data["by_application"]["CN202310000001.1"] == "150.00"
    assert data["by_application"]["CN202310000002.2"] == "200.00"
    assert data["by_fee_type"]["申请费"] == "300.00"
    assert data["by_fee_type"]["年费"] == "50.00"


def test_summarize_fees_rejects_bad_application_number() -> None:
    payload = {
        "records": [
            {"patent_application_number": "不是申请号", "fee_type": "申请费", "amount_yuan": "10.00"},
        ]
    }
    response = client.post("/api/v1/fees/summary", json=payload)

    assert response.status_code == 422


def test_summarize_fees_rejects_empty_records() -> None:
    response = client.post("/api/v1/fees/summary", json={"records": []})

    assert response.status_code == 422
