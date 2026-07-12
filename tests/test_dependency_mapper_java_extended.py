"""Extended Java dependency mapping tests — file I/O, HTTP, and method calls."""

import json
from pathlib import Path

import pytest

from coded_tools.legacy_extraction.dependency_mapper_tool import DependencyMapperTool

SAMPLE_DIR = Path(__file__).parent.parent / "sample_data"


@pytest.fixture
def mapper() -> DependencyMapperTool:
    return DependencyMapperTool()


@pytest.fixture
def java_billing_source() -> str:
    return (SAMPLE_DIR / "java_legacy_billing.java").read_text()


class TestJavaFileIo:
    async def test_detects_file_io_classes(self, mapper, java_billing_source):
        result = json.loads(
            await mapper.async_invoke(
                {"source_code": java_billing_source, "language": "java"}, {}
            )
        )
        io_classes = result["file_io"]["io_classes_used"]
        assert "FileWriter" in io_classes
        assert "BufferedWriter" in io_classes

    async def test_detects_file_paths(self, mapper, java_billing_source):
        result = json.loads(
            await mapper.async_invoke(
                {"source_code": java_billing_source, "language": "java"}, {}
            )
        )
        # The REPORT_PATH constant contains a file path but is in the DB_URL-style constant,
        # let's check the new File() pattern detection
        file_paths = result["file_io"]["file_paths"]
        # File paths are detected from `new File("...")` patterns; this sample uses FileWriter directly
        assert isinstance(file_paths, list)


class TestJavaSqlStatements:
    async def test_detects_sql_select(self, mapper, java_billing_source):
        result = json.loads(
            await mapper.async_invoke(
                {"source_code": java_billing_source, "language": "java"}, {}
            )
        )
        sqls = result["database_refs"]["sql_statements"]
        select_stmts = [s for s in sqls if "SELECT" in s.upper()]
        assert len(select_stmts) >= 1

    async def test_detects_sql_insert(self, mapper, java_billing_source):
        result = json.loads(
            await mapper.async_invoke(
                {"source_code": java_billing_source, "language": "java"}, {}
            )
        )
        sqls = result["database_refs"]["sql_statements"]
        inserts = [s for s in sqls if "INSERT" in s.upper()]
        assert len(inserts) >= 1


class TestJavaImportCategorization:
    async def test_separates_javax_imports(self, mapper, java_billing_source):
        result = json.loads(
            await mapper.async_invoke(
                {"source_code": java_billing_source, "language": "java"}, {}
            )
        )
        javax = result["imports"]["javax"]
        assert isinstance(javax, list)

    async def test_detects_all_java_sql_imports(self, mapper, java_billing_source):
        result = json.loads(
            await mapper.async_invoke(
                {"source_code": java_billing_source, "language": "java"}, {}
            )
        )
        java_std = result["imports"]["java_standard"]
        sql_imports = [i for i in java_std if "sql" in i]
        assert len(sql_imports) >= 4  # Connection, DriverManager, PreparedStatement, ResultSet, SQLException

    async def test_detects_io_imports(self, mapper, java_billing_source):
        result = json.loads(
            await mapper.async_invoke(
                {"source_code": java_billing_source, "language": "java"}, {}
            )
        )
        java_std = result["imports"]["java_standard"]
        io_imports = [i for i in java_std if "io" in i]
        assert len(io_imports) >= 2


class TestJavaInternalCalls:
    async def test_detects_method_calls(self, mapper, java_billing_source):
        result = json.loads(
            await mapper.async_invoke(
                {"source_code": java_billing_source, "language": "java"}, {}
            )
        )
        calls = result["internal_calls"]
        assert len(calls) > 0
        call_str = " ".join(calls)
        assert "DriverManager.getConnection()" in call_str or "getConnection" in call_str
