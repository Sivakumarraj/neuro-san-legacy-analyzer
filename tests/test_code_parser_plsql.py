"""Tests for PL/SQL parsing in CodeParserTool — previously zero coverage."""

import json

import pytest

from coded_tools.legacy_extraction.code_parser_tool import CodeParserTool

PLSQL_SAMPLE = """\
CREATE OR REPLACE PROCEDURE calculate_bonus(
    p_employee_id IN NUMBER,
    p_bonus_pct   IN NUMBER
) AS
    v_salary      NUMBER(10,2);
    v_bonus       NUMBER(10,2);
    v_department  VARCHAR2(50);
    CURSOR emp_cursor IS
        SELECT salary, department_name
        FROM employees e JOIN departments d ON e.dept_id = d.dept_id
        WHERE e.employee_id = p_employee_id;
BEGIN
    OPEN emp_cursor;
    FETCH emp_cursor INTO v_salary, v_department;
    CLOSE emp_cursor;

    IF v_salary > 100000 THEN
        v_bonus := v_salary * (p_bonus_pct / 2);
    ELSE
        v_bonus := v_salary * p_bonus_pct;
    END IF;

    CASE v_department
        WHEN 'SALES' THEN v_bonus := v_bonus * 1.1;
        WHEN 'ENGINEERING' THEN v_bonus := v_bonus * 1.2;
    END CASE;

    UPDATE employees SET bonus = v_bonus WHERE employee_id = p_employee_id;
    COMMIT;
END calculate_bonus;
/

CREATE OR REPLACE FUNCTION get_employee_rating(
    p_employee_id IN NUMBER
) RETURN VARCHAR2 AS
    v_rating VARCHAR2(10);
    v_years  NUMBER;
BEGIN
    SELECT years_of_service INTO v_years
    FROM employees WHERE employee_id = p_employee_id;

    IF v_years > 10 THEN
        v_rating := 'SENIOR';
    ELSE
        v_rating := 'STANDARD';
    END IF;

    FOR i IN 1..5 LOOP
        DBMS_OUTPUT.PUT_LINE('Processing iteration: ' || i);
    END LOOP;

    WHILE v_years > 0 LOOP
        v_years := v_years - 1;
    END LOOP;

    RETURN v_rating;
END get_employee_rating;
/
"""


@pytest.fixture
def parser() -> CodeParserTool:
    return CodeParserTool()


class TestPlsqlParsing:
    async def test_extracts_procedures(self, parser):
        result = json.loads(
            await parser.async_invoke({"source_code": PLSQL_SAMPLE, "language": "plsql"}, {})
        )
        assert "CALCULATE_BONUS" in result["functions"]

    async def test_extracts_functions(self, parser):
        result = json.loads(
            await parser.async_invoke({"source_code": PLSQL_SAMPLE, "language": "plsql"}, {})
        )
        assert "GET_EMPLOYEE_RATING" in result["functions"]

    async def test_extracts_variables(self, parser):
        result = json.loads(
            await parser.async_invoke({"source_code": PLSQL_SAMPLE, "language": "plsql"}, {})
        )
        names = {v["name"] for v in result["variables"]}
        assert "v_salary" in names or "V_SALARY" in names

    async def test_extracts_cursors(self, parser):
        result = json.loads(
            await parser.async_invoke({"source_code": PLSQL_SAMPLE, "language": "plsql"}, {})
        )
        cursors = result["data_structures"]["cursors"]
        assert "EMP_CURSOR" in cursors

    async def test_extracts_if_conditions(self, parser):
        result = json.loads(
            await parser.async_invoke({"source_code": PLSQL_SAMPLE, "language": "plsql"}, {})
        )
        conditions = result["control_flow"]["if_conditions"]
        assert len(conditions) >= 2

    async def test_extracts_case_blocks(self, parser):
        result = json.loads(
            await parser.async_invoke({"source_code": PLSQL_SAMPLE, "language": "plsql"}, {})
        )
        cases = result["control_flow"]["case_blocks"]
        assert len(cases) >= 1

    async def test_extracts_for_loops(self, parser):
        result = json.loads(
            await parser.async_invoke({"source_code": PLSQL_SAMPLE, "language": "plsql"}, {})
        )
        loops = result["control_flow"]["loops"]
        loop_types = [lp["type"] for lp in loops]
        assert "FOR" in loop_types

    async def test_extracts_while_loops(self, parser):
        result = json.loads(
            await parser.async_invoke({"source_code": PLSQL_SAMPLE, "language": "plsql"}, {})
        )
        loops = result["control_flow"]["loops"]
        loop_types = [lp["type"] for lp in loops]
        assert "WHILE" in loop_types

    async def test_reports_language_and_loc(self, parser):
        result = json.loads(
            await parser.async_invoke({"source_code": PLSQL_SAMPLE, "language": "plsql"}, {})
        )
        assert result["language"] == "plsql"
        assert result["lines_of_code"] > 0
