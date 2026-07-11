# ============================================================================
# test_dependency_mapper_tool.py — Unit tests for the DependencyMapperTool.
#
# WHAT THIS FILE DOES:
#   Verifies that the deterministic dependency mapper correctly traces
#   external program calls, file I/O, and imports in the bundled COBOL and
#   Java sample files.
#
# RUN WITH:
#   uv run pytest
# ============================================================================

import json
from pathlib import Path

import pytest

from coded_tools.legacy_extraction.dependency_mapper_tool import DependencyMapperTool

SAMPLE_DIR = Path(__file__).parent.parent / "sample_data"


@pytest.fixture
def mapper() -> DependencyMapperTool:
    return DependencyMapperTool()


@pytest.fixture
def cobol_payment_source() -> str:
    return (SAMPLE_DIR / "cobol_payment.cob").read_text()


@pytest.fixture
def java_billing_source() -> str:
    return (SAMPLE_DIR / "java_legacy_billing.java").read_text()


class TestCobolDependencies:
    async def test_traces_external_program_calls(self, mapper, cobol_payment_source):
        result = json.loads(
            await mapper.async_invoke(
                {"source_code": cobol_payment_source, "language": "cobol"}, {}
            )
        )
        program_calls = result["external_systems"]["program_calls"]
        for external_program in ("HIGHVAL01", "NOTIF01", "LEDGER01"):
            assert external_program in program_calls

    async def test_traces_file_assignments(self, mapper, cobol_payment_source):
        result = json.loads(
            await mapper.async_invoke(
                {"source_code": cobol_payment_source, "language": "cobol"}, {}
            )
        )
        logical_names = {
            f["logical_name"] for f in result["file_io"]["file_assignments"]
        }
        assert "PAYMENT-FILE" in logical_names
        assert "REPORT-FILE" in logical_names

    async def test_traces_internal_perform_calls(self, mapper, cobol_payment_source):
        result = json.loads(
            await mapper.async_invoke(
                {"source_code": cobol_payment_source, "language": "cobol"}, {}
            )
        )
        assert "CALCULATE-LATE-FEE" in result["internal_calls"]


class TestJavaDependencies:
    async def test_categorizes_imports(self, mapper, java_billing_source):
        result = json.loads(
            await mapper.async_invoke(
                {"source_code": java_billing_source, "language": "java"}, {}
            )
        )
        assert "java.sql.Connection" in result["imports"]["java_standard"]

    async def test_detects_jdbc_usage(self, mapper, java_billing_source):
        result = json.loads(
            await mapper.async_invoke(
                {"source_code": java_billing_source, "language": "java"}, {}
            )
        )
        assert len(result["database_refs"]["jdbc_usage"]) > 0
        assert len(result["database_refs"]["sql_statements"]) > 0

    async def test_detects_deprecated_markers(self, mapper, java_billing_source):
        result = json.loads(
            await mapper.async_invoke(
                {"source_code": java_billing_source, "language": "java"}, {}
            )
        )
        assert result["annotations"]["deprecated_markers"] >= 2


class TestErrorHandling:
    async def test_empty_source_returns_error(self, mapper):
        result = json.loads(
            await mapper.async_invoke({"source_code": "", "language": "cobol"}, {})
        )
        assert "error" in result