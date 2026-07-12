"""Tests using the cobol_inventory.cob sample — previously unused in any test."""

import json
from pathlib import Path

import pytest

from coded_tools.legacy_extraction.code_parser_tool import CodeParserTool
from coded_tools.legacy_extraction.dependency_mapper_tool import DependencyMapperTool

SAMPLE_DIR = Path(__file__).parent.parent / "sample_data"


@pytest.fixture
def parser() -> CodeParserTool:
    return CodeParserTool()


@pytest.fixture
def mapper() -> DependencyMapperTool:
    return DependencyMapperTool()


@pytest.fixture
def cobol_inventory_source() -> str:
    return (SAMPLE_DIR / "cobol_inventory.cob").read_text()


class TestInventoryParsing:
    async def test_extracts_paragraphs(self, parser, cobol_inventory_source):
        result = json.loads(
            await parser.async_invoke(
                {"source_code": cobol_inventory_source, "language": "cobol"}, {}
            )
        )
        for para in ("MAIN-PROCESS", "CHECK-INVENTORY", "TRIGGER-REORDER",
                     "CALCULATE-ITEM-VALUE", "DISPLAY-SUMMARY"):
            assert para in result["functions"]

    async def test_extracts_inventory_variables(self, parser, cobol_inventory_source):
        result = json.loads(
            await parser.async_invoke(
                {"source_code": cobol_inventory_source, "language": "cobol"}, {}
            )
        )
        names = {v["name"] for v in result["variables"]}
        assert "WS-REORDER-COUNT" in names
        assert "WS-CRITICAL-THRESHOLD" in names
        assert "INV-PRODUCT-ID" in names

    async def test_extracts_compute_statements(self, parser, cobol_inventory_source):
        result = json.loads(
            await parser.async_invoke(
                {"source_code": cobol_inventory_source, "language": "cobol"}, {}
            )
        )
        targets = {c["target"] for c in result["data_structures"]["compute_statements"]}
        assert "WS-ITEM-VALUE" in targets

    async def test_extracts_if_conditions(self, parser, cobol_inventory_source):
        result = json.loads(
            await parser.async_invoke(
                {"source_code": cobol_inventory_source, "language": "cobol"}, {}
            )
        )
        ifs = result["control_flow"]["if_conditions"]
        assert len(ifs) >= 2


class TestInventoryDependencies:
    async def test_traces_alert_program_call(self, mapper, cobol_inventory_source):
        result = json.loads(
            await mapper.async_invoke(
                {"source_code": cobol_inventory_source, "language": "cobol"}, {}
            )
        )
        program_calls = result["external_systems"]["program_calls"]
        assert "ALERT01" in program_calls

    async def test_traces_reorder_program_call(self, mapper, cobol_inventory_source):
        result = json.loads(
            await mapper.async_invoke(
                {"source_code": cobol_inventory_source, "language": "cobol"}, {}
            )
        )
        program_calls = result["external_systems"]["program_calls"]
        assert "REORDER01" in program_calls

    async def test_traces_indexed_file(self, mapper, cobol_inventory_source):
        result = json.loads(
            await mapper.async_invoke(
                {"source_code": cobol_inventory_source, "language": "cobol"}, {}
            )
        )
        logical_names = {
            f["logical_name"] for f in result["file_io"]["file_assignments"]
        }
        assert "INVENTORY-FILE" in logical_names

    async def test_traces_internal_performs(self, mapper, cobol_inventory_source):
        result = json.loads(
            await mapper.async_invoke(
                {"source_code": cobol_inventory_source, "language": "cobol"}, {}
            )
        )
        assert "CHECK-INVENTORY" in result["internal_calls"]
        assert "TRIGGER-REORDER" in result["internal_calls"]
