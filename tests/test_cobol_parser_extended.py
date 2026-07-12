"""Extended COBOL parser tests — control flow and data structures not covered by originals."""

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


class TestCobolControlFlow:
    async def test_extracts_if_conditions(self, parser, cobol_payment_source):
        result = json.loads(
            await parser.async_invoke(
                {"source_code": cobol_payment_source, "language": "cobol"}, {}
            )
        )
        ifs = result["control_flow"]["if_conditions"]
        assert len(ifs) >= 2

    async def test_extracts_goto_statements(self, parser):
        source = """\
       IDENTIFICATION DIVISION.
       PROGRAM-ID. GOTO-TEST.
       PROCEDURE DIVISION.
       PARA-A.
           IF X > 5
               GO TO PARA-B
           END-IF.
       PARA-B.
           STOP RUN.
"""
        result = json.loads(
            await parser.async_invoke({"source_code": source, "language": "cobol"}, {})
        )
        assert "PARA-B" in result["control_flow"]["goto_statements"]

    async def test_extracts_evaluate_blocks(self, parser):
        source = """\
       IDENTIFICATION DIVISION.
       PROGRAM-ID. EVAL-TEST.
       PROCEDURE DIVISION.
       MAIN-PARA.
           EVALUATE WS-STATUS
               WHEN 'A' PERFORM HANDLE-ACTIVE
               WHEN 'I' PERFORM HANDLE-INACTIVE
           END-EVALUATE.
           STOP RUN.
"""
        result = json.loads(
            await parser.async_invoke({"source_code": source, "language": "cobol"}, {})
        )
        evaluates = result["control_flow"]["evaluate_blocks"]
        assert len(evaluates) >= 1


class TestCobolDataStructures:
    async def test_extracts_divisions(self, parser, cobol_payment_source):
        result = json.loads(
            await parser.async_invoke(
                {"source_code": cobol_payment_source, "language": "cobol"}, {}
            )
        )
        divisions = [d.strip() for d in result["data_structures"]["divisions"]]
        assert "IDENTIFICATION" in divisions
        assert "PROCEDURE" in divisions

    async def test_extracts_move_statements(self, parser, cobol_payment_source):
        result = json.loads(
            await parser.async_invoke(
                {"source_code": cobol_payment_source, "language": "cobol"}, {}
            )
        )
        moves = result["data_structures"]["move_statements"]
        assert len(moves) >= 1
        targets = {m["target"] for m in moves}
        assert "WS-EOF-FLAG" in targets or "WS-HIGH-VALUE-FLAG" in targets

    async def test_extracts_variable_picture_clauses(self, parser, cobol_payment_source):
        result = json.loads(
            await parser.async_invoke(
                {"source_code": cobol_payment_source, "language": "cobol"}, {}
            )
        )
        by_name = {v["name"]: v for v in result["variables"]}
        assert "9(7)V99" in by_name["WS-LATE-FEE"]["picture"]


class TestCobolDependencyExtended:
    """Extended COBOL dependency tests for file operations and copybooks."""

    async def test_traces_file_operations(self, parser):
        """Verify file_operations in dependency mapper captures OPEN/CLOSE."""
        from coded_tools.legacy_extraction.dependency_mapper_tool import DependencyMapperTool
        mapper = DependencyMapperTool()
        source = (SAMPLE_DIR / "cobol_payment.cob").read_text()
        result = json.loads(
            await mapper.async_invoke({"source_code": source, "language": "cobol"}, {})
        )
        operations = {f["operation"] for f in result["file_io"]["file_operations"]}
        assert "OPEN" in operations
        assert "CLOSE" in operations
        assert "READ" in operations

    async def test_traces_copybooks(self, parser):
        """Verify COPY statements are detected."""
        from coded_tools.legacy_extraction.dependency_mapper_tool import DependencyMapperTool
        mapper = DependencyMapperTool()
        source = """\
       IDENTIFICATION DIVISION.
       PROGRAM-ID. COPY-TEST.
       DATA DIVISION.
       WORKING-STORAGE SECTION.
           COPY CUSTOMER-RECORD.
           COPY PAYMENT-LAYOUT.
       PROCEDURE DIVISION.
       MAIN-PARA.
           STOP RUN.
"""
        result = json.loads(
            await mapper.async_invoke({"source_code": source, "language": "cobol"}, {})
        )
        assert "CUSTOMER-RECORD" in result["imports"]
        assert "PAYMENT-LAYOUT" in result["imports"]
