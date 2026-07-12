"""Extended Java parser tests — previously only 1 test existed for Java."""

import json
from pathlib import Path

import pytest

from coded_tools.legacy_extraction.code_parser_tool import CodeParserTool

SAMPLE_DIR = Path(__file__).parent.parent / "sample_data"


@pytest.fixture
def parser() -> CodeParserTool:
    return CodeParserTool()


@pytest.fixture
def java_billing_source() -> str:
    return (SAMPLE_DIR / "java_legacy_billing.java").read_text()


class TestJavaVariableExtraction:
    async def test_extracts_field_variables(self, parser, java_billing_source):
        result = json.loads(
            await parser.async_invoke(
                {"source_code": java_billing_source, "language": "java"}, {}
            )
        )
        names = {v["name"] for v in result["variables"]}
        assert "DB_URL" in names
        assert "dbConnection" in names

    async def test_extracts_variable_types(self, parser, java_billing_source):
        result = json.loads(
            await parser.async_invoke(
                {"source_code": java_billing_source, "language": "java"}, {}
            )
        )
        type_map = {v["name"]: v["type"] for v in result["variables"]}
        assert type_map.get("dbConnection") == "Connection"


class TestJavaControlFlow:
    async def test_extracts_if_conditions(self, parser, java_billing_source):
        result = json.loads(
            await parser.async_invoke(
                {"source_code": java_billing_source, "language": "java"}, {}
            )
        )
        ifs = result["control_flow"]["if_conditions"]
        assert len(ifs) >= 3  # tiered discount has multiple ifs

    async def test_extracts_try_catch_blocks(self, parser, java_billing_source):
        result = json.loads(
            await parser.async_invoke(
                {"source_code": java_billing_source, "language": "java"}, {}
            )
        )
        catches = result["control_flow"]["try_catch_blocks"]
        assert len(catches) >= 1

    async def test_extracts_for_loops(self, parser, java_billing_source):
        result = json.loads(
            await parser.async_invoke(
                {"source_code": java_billing_source, "language": "java"}, {}
            )
        )
        for_loops = result["control_flow"]["for_loops"]
        assert len(for_loops) >= 1

    async def test_extracts_while_loops(self, parser, java_billing_source):
        result = json.loads(
            await parser.async_invoke(
                {"source_code": java_billing_source, "language": "java"}, {}
            )
        )
        whiles = result["control_flow"]["while_loops"]
        assert len(whiles) >= 1


class TestJavaMethodCalls:
    async def test_extracts_method_calls(self, parser, java_billing_source):
        result = json.loads(
            await parser.async_invoke(
                {"source_code": java_billing_source, "language": "java"}, {}
            )
        )
        calls = result["data_structures"]["method_calls"]
        assert len(calls) > 0
        call_str = " ".join(calls)
        assert "getConnection" in call_str or "DriverManager" in call_str


class TestJavaMetadata:
    async def test_reports_all_methods(self, parser, java_billing_source):
        result = json.loads(
            await parser.async_invoke(
                {"source_code": java_billing_source, "language": "java"}, {}
            )
        )
        method_names = result["functions"]
        assert "initializeConnection" in method_names
        assert "processMonthlyBilling" in method_names
        assert "generateBillingReport" in method_names
        assert "closeConnection" in method_names

    async def test_reports_language_and_loc(self, parser, java_billing_source):
        result = json.loads(
            await parser.async_invoke(
                {"source_code": java_billing_source, "language": "java"}, {}
            )
        )
        assert result["language"] == "java"
        assert result["lines_of_code"] > 100

    async def test_method_details_include_return_types(self, parser, java_billing_source):
        result = json.loads(
            await parser.async_invoke(
                {"source_code": java_billing_source, "language": "java"}, {}
            )
        )
        methods = result["methods"]
        by_name = {m["name"]: m for m in methods}
        assert by_name["calculateInvoiceTotal"]["return_type"] == "double"
        assert by_name["initializeConnection"]["return_type"] == "void"
