import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from fee_calc import calculate, run


VALID = [
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


class FeeCalculatorTests(unittest.TestCase):
    def test_multiple_records_are_summarized(self) -> None:
        result = calculate(VALID)
        self.assertEqual(result["record_count"], 3)
        self.assertEqual(result["by_application"]["CN202410123456.7"], "4400.50")
        self.assertEqual(result["by_fee_type"]["代理服务费"], "4700.00")
        self.assertEqual(result["total_yuan"], "5600.50")

    def test_empty_array_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            calculate([])

    def test_missing_field_is_rejected(self) -> None:
        record = VALID[0] | {"amount_yuan": "1.00"}
        del record["fee_type"]
        with self.assertRaises(ValueError):
            calculate([record])

    def test_extra_field_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            calculate([VALID[0] | {"currency": "CNY"}])

    def test_invalid_amounts_are_rejected(self) -> None:
        for value in ("0", "-1", "abc", "10.001"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                calculate([VALID[0] | {"amount_yuan": value}])

    def test_bad_patent_number_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            calculate([VALID[0] | {"patent_application_number": "unknown"}])

    def test_broken_json_does_not_overwrite_output(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / "broken.json"
            output = root / "summary.json"
            source.write_text("{", encoding="utf-8")
            output.write_text("old result", encoding="utf-8")
            with redirect_stderr(io.StringIO()):
                self.assertEqual(run([str(source), "-o", str(output)]), 1)
            self.assertEqual(output.read_text(encoding="utf-8"), "old result")

    def test_input_cannot_be_output(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "fees.json"
            original = json.dumps(VALID, ensure_ascii=False)
            source.write_text(original, encoding="utf-8")
            with redirect_stderr(io.StringIO()):
                self.assertEqual(run([str(source), "-o", str(source)]), 1)
            self.assertEqual(source.read_text(encoding="utf-8"), original)

    def test_cli_writes_valid_json(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / "fees.json"
            output = root / "summary.json"
            source.write_text(json.dumps(VALID, ensure_ascii=False), encoding="utf-8")
            with redirect_stdout(io.StringIO()):
                self.assertEqual(run([str(source), "-o", str(output)]), 0)
            self.assertEqual(json.loads(output.read_text(encoding="utf-8"))["total_yuan"], "5600.50")


if __name__ == "__main__":
    unittest.main()
