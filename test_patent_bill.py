import unittest

from patent_bill import build_result, validate


VALID = {
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


class PatentBillTests(unittest.TestCase):
    def test_valid_record_uses_standard_review(self) -> None:
        self.assertEqual(build_result(VALID.copy())["route"], "standard_manual_review")

    def test_low_confidence_uses_priority_review(self) -> None:
        record = VALID | {"confidence": 0.5}
        self.assertIn("模型置信度低于 0.85", build_result(record)["review_reasons"])

    def test_bad_number_uses_priority_review(self) -> None:
        record = VALID | {"patent_application_number": "unknown"}
        self.assertEqual(build_result(record)["route"], "priority_manual_review")

    def test_missing_amount_uses_priority_review(self) -> None:
        record = VALID | {"amount_yuan": None}
        self.assertIn("缺少金额", build_result(record)["review_reasons"])

    def test_extra_field_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            validate(VALID | {"approved": True})


if __name__ == "__main__":
    unittest.main()
