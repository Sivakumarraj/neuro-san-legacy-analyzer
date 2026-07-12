"""Edge case and boundary condition tests for both tools."""

import json

import pytest

from coded_tools.legacy_extraction.code_parser_tool import CodeParserTool
from coded_tools.legacy_extraction.dependency_mapper_tool import DependencyMapperTool


@pytest.fixture
def parser() -> CodeParserTool:
    return CodeParserTool()


@pytest.fixture
def mapper() -> DependencyMapperTool:
    return DependencyMapperTool()


class TestCodeParserEdgeCases:
    async def test_whitespace_only_source_returns_error(self, parser):
        result = json.loads(
            await parser.async_invoke({"source_code": "   \n\t\n  ", "language": "cobol"}, {})
        )
        assert "error" in result

    async def test_language_with_whitespace_and_mixed_case(self, parser):
        source = "       IDENTIFICATION DIVISION.\n       PROGRAM-ID. TEST."
        result = json.loads(
            await parser.async_invoke({"source_code": source, "language": "  COBOL  "}, {})
        )
        assert result["language"] == "cobol"
        assert "error" not in result

    async def test_missing_language_key(self, parser):
        result = json.loads(
            await parser.async_invoke({"source_code": "some code"}, {})
        )
        assert "error" in result

    async def test_missing_source_code_key(self, parser):
        result = json.loads(
            await parser.async_invoke({"language": "java"}, {})
        )
        assert "error" in result

    async def test_sly_data_none_is_accepted(self, parser):
        source = "public class Foo { public void bar() {} }"
        result = json.loads(
            await parser.async_invoke({"source_code": source, "language": "java"}, None)
        )
        assert "Foo" in result["classes"]

    async def test_empty_args_dict(self, parser):
        result = json.loads(await parser.async_invoke({}, {}))
        assert "error" in result

    async def test_cobol_with_no_procedure_division(self, parser):
        source = """\
       IDENTIFICATION DIVISION.
       PROGRAM-ID. EMPTY-PROG.
       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01 WS-DUMMY PIC X(10).
"""
        result = json.loads(
            await parser.async_invoke({"source_code": source, "language": "cobol"}, {})
        )
        assert result["language"] == "cobol"
        assert len(result["variables"]) >= 1

    async def test_java_with_no_methods(self, parser):
        source = "public class EmptyClass { private int x = 5; }"
        result = json.loads(
            await parser.async_invoke({"source_code": source, "language": "java"}, {})
        )
        assert "EmptyClass" in result["classes"]
        assert result["functions"] == []

    async def test_plsql_with_only_anonymous_block(self, parser):
        source = """\
BEGIN
    DBMS_OUTPUT.PUT_LINE('Hello');
END;
/
"""
        result = json.loads(
            await parser.async_invoke({"source_code": source, "language": "plsql"}, {})
        )
        assert result["language"] == "plsql"
        assert result["functions"] == []


class TestDependencyMapperEdgeCases:
    async def test_whitespace_only_source_returns_error(self, mapper):
        result = json.loads(
            await mapper.async_invoke({"source_code": "\n\n\n", "language": "java"}, {})
        )
        assert "error" in result

    async def test_language_case_insensitive(self, mapper):
        source = "import java.util.List;"
        result = json.loads(
            await mapper.async_invoke({"source_code": source, "language": "JAVA"}, {})
        )
        assert result["language"] == "java"

    async def test_unsupported_language_returns_error(self, mapper):
        result = json.loads(
            await mapper.async_invoke(
                {"source_code": "print('hi')", "language": "python"}, {}
            )
        )
        assert "error" in result

    async def test_missing_keys_returns_error(self, mapper):
        result = json.loads(await mapper.async_invoke({}, {}))
        assert "error" in result

    async def test_sly_data_none_is_accepted(self, mapper):
        source = "import java.util.List;"
        result = json.loads(
            await mapper.async_invoke({"source_code": source, "language": "java"}, None)
        )
        assert "error" not in result

    async def test_cobol_with_no_dependencies(self, mapper):
        source = """\
       IDENTIFICATION DIVISION.
       PROGRAM-ID. MINIMAL.
       PROCEDURE DIVISION.
       MAIN-PARA.
           DISPLAY 'HELLO'.
           STOP RUN.
"""
        result = json.loads(
            await mapper.async_invoke({"source_code": source, "language": "cobol"}, {})
        )
        assert result["external_systems"]["program_calls"] == []
        assert result["file_io"]["file_assignments"] == []
        assert result["database_refs"] == []

    async def test_java_with_no_imports(self, mapper):
        source = "public class NoImports { public void run() { System.out.println(1); } }"
        result = json.loads(
            await mapper.async_invoke({"source_code": source, "language": "java"}, {})
        )
        assert result["imports"]["java_standard"] == []
        assert result["imports"]["third_party"] == []

    async def test_plsql_without_utl_file(self, mapper):
        source = """\
BEGIN
    DBMS_OUTPUT.PUT_LINE('No file usage here');
END;
/
"""
        result = json.loads(
            await mapper.async_invoke({"source_code": source, "language": "plsql"}, {})
        )
        assert result["file_io"]["utl_file_usage"] is False
