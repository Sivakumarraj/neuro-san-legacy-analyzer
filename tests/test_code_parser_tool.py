# ============================================================================
# test_code_parser_tool.py — Unit tests for the CodeParserTool CodedTool.
#
# WHAT THIS FILE DOES:
#   Verifies that the deterministic code parser correctly extracts structure
#   from the bundled COBOL and Java sample files. Because the parser is a
#   CodedTool (pure regex, no LLM), its output is fully testable — same
#   input always produces the same output.
#
# RUN WITH:
#   uv run pytest
# ============================================================================

import json
from pathlib import Path

import pytest

from coded_tools.legacy_extraction.code_parser_tool import CodeParserTool

SAMPLE_DIR = Path(__file__).parent.parent / "sample_data"


@pytest.fixture
def parser() -> CodeParserTool:
    return CodeParserTool()


@pytest.fixture
def cobol_payment_source() -> str:
    return (SAMPLE_DIR / "cobol_payment.cob").read_text()


@pytest.fixture
def java_billing_source() -> str:
    return (SAMPLE_DIR / "java_legacy_billing.java").read_text()


class TestCobolParsing:
    async def test_extracts_paragraphs(self, parser, cobol_payment_source):
        result = json.loads(
            await parser.async_invoke(
                {"source_code": cobol_payment_source, "language": "cobol"}, {}
            )
        )
        for paragraph in ("MAIN-PROCESS", "READ-PAYMENT", "CALCULATE-LATE-FEE",
                          "UPDATE-LEDGER", "GENERATE-SUMMARY"):
            assert paragraph in result["functions"]

    async def test_extracts_working_storage_variables(self, parser, cobol_payment_source):
        result = json.loads(
            await parser.async_invoke(
                {"source_code": cobol_payment_source, "language": "cobol"}, {}
            )
        )
        names = {v["name"] for v in result["variables"]}
        assert "WS-LATE-FEE" in names
        assert "WS-DAYS-OVERDUE" in names

    async def test_extracts_business_calculations(self, parser, cobol_payment_source):
        result = json.loads(
            await parser.async_invoke(
                {"source_code": cobol_payment_source, "language": "cobol"}, {}
            )
        )
        compute_targets = {
            c["target"] for c in result["data_structures"]["compute_statements"]
        }
        assert "WS-LATE-FEE" in compute_targets

    async def test_extracts_perform_calls(self, parser, cobol_payment_source):
        result = json.loads(
            await parser.async_invoke(
                {"source_code": cobol_payment_source, "language": "cobol"}, {}
            )
        )
        assert "CALCULATE-LATE-FEE" in result["control_flow"]["perform_calls"]

    async def test_reports_language_and_loc(self, parser, cobol_payment_source):
        result = json.loads(
            await parser.async_invoke(
                {"source_code": cobol_payment_source, "language": "cobol"}, {}
            )
        )
        assert result["language"] == "cobol"
        assert result["lines_of_code"] > 0


class TestJavaParsing:
    async def test_extracts_class_and_methods(self, parser, java_billing_source):
        result = json.loads(
            await parser.async_invoke(
                {"source_code": java_billing_source, "language": "java"}, {}
            )
        )
        assert "LegacyBillingService" in result["classes"]
        assert "calculateInvoiceTotal" in result["functions"]
        assert "calculateTieredDiscount" in result["functions"]


class TestErrorHandling:
    async def test_empty_source_returns_error(self, parser):
        result = json.loads(
            await parser.async_invoke({"source_code": "", "language": "cobol"}, {})
        )
        assert "error" in result

    async def test_unsupported_language_returns_error(self, parser):
        result = json.loads(
            await parser.async_invoke(
                {"source_code": "print('hi')", "language": "python"}, {}
            )
        )
        assert "error" in result