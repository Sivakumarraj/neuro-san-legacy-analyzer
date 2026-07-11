# ============================================================================
# dependency_mapper_tool.py — Deterministic Dependency Mapper (CodedTool)
#
# WHAT THIS FILE DOES:
#   Scans legacy source code and traces all dependencies: internal function
#   calls, external system references (databases, files, APIs), imports,
#   and copybook includes. Returns a structured map of everything the code
#   touches.
#
# HOW IT CONNECTS:
#   The Front-Man orchestrator calls this tool alongside the CodeParser.
#   The dependency map is then passed to the MigrationRiskAssessor (to flag
#   risky external couplings) and the SpecGenerator (to document what systems
#   the modernized code will need to interface with).
#
# WHY CodedTool (NOT LLM):
#   Dependency tracing is PATTERN MATCHING — "CALL 'PAYMOD01'" in COBOL,
#   "import java.sql.*" in Java. These are exact string patterns, not
#   judgment calls. An LLM would be slower, more expensive, and could
#   hallucinate dependencies that don't exist.
# ============================================================================

import json
import re
import logging
from typing import Any, Dict, List

from neuro_san.interfaces.coded_tool import CodedTool

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DependencyMapperTool(CodedTool):
    """
    Deterministically traces dependencies in legacy source code.

    Supported languages: COBOL, Java, PL/SQL.
    Returns a JSON object with: internal_calls, external_systems,
    file_io, database_refs, imports.
    """

    async def async_invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any] = None) -> str:
        """
        Main entry point called by the Neuro SAN framework.

        Args:
            args: Dictionary with keys:
                - source_code (str): The legacy source code to analyze.
                - language (str): One of "cobol", "java", "plsql".
            sly_data: Private data channel (not used by this tool).

        Returns:
            JSON string with the dependency map.
        """
        source_code = args.get("source_code", "")
        language = args.get("language", "").lower().strip()

        logger.info("DependencyMapperTool invoked for language: %s", language)

        if not source_code.strip():
            return json.dumps({"error": "No source code provided."})

        # Dispatch to the right mapper based on language
        if language == "cobol":
            result = self._map_cobol(source_code)
        elif language == "java":
            result = self._map_java(source_code)
        elif language == "plsql":
            result = self._map_plsql(source_code)
        else:
            return json.dumps({
                "error": f"Unsupported language: '{language}'. Supported: cobol, java, plsql."
            })

        result["language"] = language
        return json.dumps(result, indent=2)

    # -------------------------------------------------------------------------
    # COBOL Dependency Mapper
    # -------------------------------------------------------------------------
    def _map_cobol(self, code: str) -> Dict[str, Any]:
        """Trace dependencies in COBOL source code."""
        upper_code = code.upper()

        # CALL statements — calls to external programs/modules
        # Pattern: CALL 'PROGRAM-NAME' or CALL VARIABLE-NAME
        external_calls = re.findall(
            r"CALL\s+'([\w-]+)'",
            upper_code
        )
        variable_calls = re.findall(
            r'CALL\s+([\w-]+)(?:\s+USING)?',
            upper_code
        )
        # Filter out quoted calls from variable calls
        variable_calls = [
            c for c in variable_calls
            if c not in external_calls and c != "USING"
        ]

        # COPY/INCLUDE — copybook includes
        copybooks = re.findall(
            r'COPY\s+([\w-]+)',
            upper_code
        )

        # File I/O — SELECT/ASSIGN, OPEN, READ, WRITE
        file_selects = re.findall(
            r'SELECT\s+([\w-]+)\s+ASSIGN\s+TO\s+([\w\'-]+)',
            upper_code
        )
        file_operations = re.findall(
            r'(OPEN|READ|WRITE|CLOSE|REWRITE|DELETE)\s+([\w-]+)',
            upper_code
        )

        # Database references — EXEC SQL blocks (DB2, etc.)
        sql_blocks = re.findall(
            r'EXEC\s+SQL\s+(.*?)END-EXEC',
            upper_code,
            re.DOTALL
        )
        sql_operations = []
        for block in sql_blocks:
            block_clean = " ".join(block.split())
            sql_operations.append(block_clean[:200])

        # PERFORM statements — internal paragraph/section calls
        performs = re.findall(
            r'PERFORM\s+([\w-]+)',
            upper_code
        )

        # CICS transactions (if any)
        cics_calls = re.findall(
            r'EXEC\s+CICS\s+(\w+)',
            upper_code
        )

        return {
            "internal_calls": list(set(performs)),
            "external_systems": {
                "program_calls": list(set(external_calls)),
                "variable_calls": list(set(variable_calls)),
                "cics_transactions": list(set(cics_calls)),
            },
            "file_io": {
                "file_assignments": [
                    {"logical_name": f[0], "physical_name": f[1]}
                    for f in file_selects
                ],
                "file_operations": [
                    {"operation": f[0], "file": f[1]}
                    for f in file_operations
                ],
            },
            "database_refs": sql_operations,
            "imports": list(set(copybooks)),
        }

    # -------------------------------------------------------------------------
    # Java Dependency Mapper
    # -------------------------------------------------------------------------
    def _map_java(self, code: str) -> Dict[str, Any]:
        """Trace dependencies in Java source code."""

        # Import statements
        imports = re.findall(
            r'import\s+([\w.]+(?:\.\*)?)\s*;',
            code
        )

        # Categorize imports
        java_std = [i for i in imports if i.startswith("java.")]
        javax_imports = [i for i in imports if i.startswith("javax.")]
        third_party = [i for i in imports if not i.startswith(("java.", "javax."))]

        # Database references — JDBC, DataSource, SQL
        jdbc_refs = re.findall(
            r'(DriverManager\.getConnection|DataSource|PreparedStatement|ResultSet|Statement|Connection)\s*',
            code
        )
        sql_strings = re.findall(
            r'(?:\"|\')((?:SELECT|INSERT|UPDATE|DELETE|CREATE|DROP|ALTER)\s+.+?)(?:\"|\')',
            code,
            re.IGNORECASE
        )

        # File I/O — FileReader, BufferedReader, FileWriter, etc.
        file_io_classes = re.findall(
            r'new\s+(File(?:Reader|Writer|InputStream|OutputStream)|BufferedReader|BufferedWriter|PrintWriter|Scanner)\s*\(',
            code
        )
        file_paths = re.findall(
            r'new\s+File\s*\(\s*["\'](.+?)["\']\s*\)',
            code
        )

        # HTTP/Network calls
        http_refs = re.findall(
            r'(HttpURLConnection|HttpClient|URL|Socket|ServerSocket)\s*',
            code
        )
        url_strings = re.findall(
            r'(?:\")(https?://[^\"]+)(?:\")',
            code
        )

        # Method calls (object.method pattern)
        method_calls = re.findall(
            r'(\w+)\s*\.\s*(\w+)\s*\(',
            code
        )
        internal_calls = list(set(
            f"{mc[0]}.{mc[1]}()"
            for mc in method_calls
        ))

        # Deprecated API usage
        deprecated = re.findall(
            r'@Deprecated|@SuppressWarnings',
            code
        )

        return {
            "internal_calls": internal_calls[:30],
            "external_systems": {
                "http_network": list(set(http_refs)),
                "urls": url_strings,
            },
            "file_io": {
                "io_classes_used": list(set(file_io_classes)),
                "file_paths": file_paths,
            },
            "database_refs": {
                "jdbc_usage": list(set(jdbc_refs)),
                "sql_statements": [s[:200] for s in sql_strings],
            },
            "imports": {
                "java_standard": java_std,
                "javax": javax_imports,
                "third_party": third_party,
            },
            "annotations": {
                "deprecated_markers": len(deprecated),
            },
        }

    # -------------------------------------------------------------------------
    # PL/SQL Dependency Mapper
    # -------------------------------------------------------------------------
    def _map_plsql(self, code: str) -> Dict[str, Any]:
        """Trace dependencies in PL/SQL source code."""
        upper_code = code.upper()

        # Package references
        package_refs = re.findall(
            r'(\w+)\.(\w+)\s*\(',
            code
        )
        package_calls = list(set(
            f"{p[0]}.{p[1]}()"
            for p in package_refs
        ))

        # DBMS_* built-in package usage
        dbms_calls = re.findall(
            r'(DBMS_\w+)\.\w+',
            upper_code
        )

        # UTL_FILE and other utility usage
        utl_calls = re.findall(
            r'(UTL_\w+)\.\w+',
            upper_code
        )

        # Table references from SQL statements
        table_refs_from = re.findall(
            r'(?:FROM|JOIN|INTO|UPDATE|DELETE\s+FROM)\s+(\w+)',
            upper_code
        )

        # External procedure/function calls
        external_calls = re.findall(
            r'(?:EXECUTE\s+IMMEDIATE|CALL)\s+[\'"]?(\w+)',
            upper_code
        )

        # Cursor references
        cursor_queries = re.findall(
            r'CURSOR\s+\w+\s+IS\s+(SELECT.+?);',
            upper_code,
            re.DOTALL
        )

        # Database link references
        db_links = re.findall(
            r'@(\w+)',
            code
        )

        return {
            "internal_calls": package_calls[:30],
            "external_systems": {
                "dbms_packages": list(set(dbms_calls)),
                "utl_packages": list(set(utl_calls)),
                "external_procedures": list(set(external_calls)),
                "database_links": list(set(db_links)),
            },
            "file_io": {
                "utl_file_usage": "UTL_FILE" in upper_code,
            },
            "database_refs": {
                "tables_referenced": list(set(table_refs_from))[:30],
                "cursor_queries": [q.strip()[:200] for q in cursor_queries],
            },
            "imports": [],
        }
