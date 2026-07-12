"""Tests for PL/SQL dependency mapping — previously zero coverage."""

import json

import pytest

from coded_tools.legacy_extraction.dependency_mapper_tool import DependencyMapperTool

PLSQL_SAMPLE = """\
CREATE OR REPLACE PROCEDURE sync_inventory AS
    v_count NUMBER;
    CURSOR item_cursor IS
        SELECT product_id, quantity FROM inventory WHERE status = 'ACTIVE';
BEGIN
    DBMS_OUTPUT.PUT_LINE('Starting inventory sync');
    DBMS_JOB.SUBMIT(v_count, 'sync_inventory', SYSDATE + 1);

    UTL_FILE.FOPEN('/export/data', 'inventory_export.csv', 'W');
    UTL_HTTP.REQUEST('http://api.warehouse.internal/sync');

    FOR rec IN item_cursor LOOP
        UPDATE warehouse_stock@REMOTE_DB SET qty = rec.quantity
        WHERE product_id = rec.product_id;

        INSERT INTO audit_log (action, item_id, timestamp)
        VALUES ('SYNC', rec.product_id, SYSDATE);

        pkg_notifications.send_update(rec.product_id);
    END LOOP;

    EXECUTE IMMEDIATE 'TRUNCATE TABLE temp_inventory';
    CALL cleanup_orphans;

    DELETE FROM staging_table WHERE processed = 'Y';
    COMMIT;
END sync_inventory;
/
"""


@pytest.fixture
def mapper() -> DependencyMapperTool:
    return DependencyMapperTool()


class TestPlsqlDependencies:
    async def test_detects_dbms_package_usage(self, mapper):
        result = json.loads(
            await mapper.async_invoke({"source_code": PLSQL_SAMPLE, "language": "plsql"}, {})
        )
        dbms = result["external_systems"]["dbms_packages"]
        assert "DBMS_OUTPUT" in dbms
        assert "DBMS_JOB" in dbms

    async def test_detects_utl_package_usage(self, mapper):
        result = json.loads(
            await mapper.async_invoke({"source_code": PLSQL_SAMPLE, "language": "plsql"}, {})
        )
        utl = result["external_systems"]["utl_packages"]
        assert "UTL_FILE" in utl
        assert "UTL_HTTP" in utl

    async def test_detects_utl_file_flag(self, mapper):
        result = json.loads(
            await mapper.async_invoke({"source_code": PLSQL_SAMPLE, "language": "plsql"}, {})
        )
        assert result["file_io"]["utl_file_usage"] is True

    async def test_detects_database_links(self, mapper):
        result = json.loads(
            await mapper.async_invoke({"source_code": PLSQL_SAMPLE, "language": "plsql"}, {})
        )
        links = result["external_systems"]["database_links"]
        assert "REMOTE_DB" in links

    async def test_detects_table_references(self, mapper):
        result = json.loads(
            await mapper.async_invoke({"source_code": PLSQL_SAMPLE, "language": "plsql"}, {})
        )
        tables = result["database_refs"]["tables_referenced"]
        assert "INVENTORY" in tables
        assert "AUDIT_LOG" in tables

    async def test_detects_cursor_queries(self, mapper):
        result = json.loads(
            await mapper.async_invoke({"source_code": PLSQL_SAMPLE, "language": "plsql"}, {})
        )
        cursors = result["database_refs"]["cursor_queries"]
        assert len(cursors) >= 1
        assert "PRODUCT_ID" in cursors[0]

    async def test_detects_external_procedure_calls(self, mapper):
        result = json.loads(
            await mapper.async_invoke({"source_code": PLSQL_SAMPLE, "language": "plsql"}, {})
        )
        external = result["external_systems"]["external_procedures"]
        assert len(external) >= 1

    async def test_detects_package_method_calls(self, mapper):
        result = json.loads(
            await mapper.async_invoke({"source_code": PLSQL_SAMPLE, "language": "plsql"}, {})
        )
        calls = result["internal_calls"]
        matching = [c for c in calls if "pkg_notifications" in c.lower() or "send_update" in c.lower()]
        assert len(matching) >= 1

    async def test_reports_language(self, mapper):
        result = json.loads(
            await mapper.async_invoke({"source_code": PLSQL_SAMPLE, "language": "plsql"}, {})
        )
        assert result["language"] == "plsql"
