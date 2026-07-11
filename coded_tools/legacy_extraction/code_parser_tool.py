# ============================================================================
# code_parser_tool.py — Deterministic Code Parser (CodedTool)
#
# WHAT THIS FILE DOES:
#   Parses legacy source code (COBOL, Java, PL/SQL) and extracts its structure:
#   functions/paragraphs, variables, control flow, and data structures.
#   This is a CodedTool (not an LLM agent) because parsing is DETERMINISTIC —
#   we use regex patterns to find known syntax, so we get consistent results
#   every time with zero hallucination risk.
#
# HOW IT CONNECTS:
#   The Front-Man orchestrator calls this tool first with the user's source code.
#   The structured JSON output is then passed to the BusinessRuleExtractor
#   (which uses an LLM to INTERPRET what the code does in plain English) and
#   the MigrationRiskAssessor (which uses an LLM to JUDGE risk levels).
#
# WHY CodedTool (NOT LLM):
#   Parsing code structure is pattern-matching, not judgment. A regex will
#   always find "PERFORM CALCULATE-LATE-FEE" in COBOL — an LLM might miss it
#   or hallucinate extra functions. Determinism = reliability.
# ============================================================================

import json
import re
import logging
from typing import Any, Dict

from neuro_san.interfaces.coded_tool import CodedTool

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CodeParserTool(CodedTool):
    """
    Deterministically parses legacy source code and extracts structural elements.

    Supported languages: COBOL, Java, PL/SQL.
    Returns a JSON object with: functions, variables, control_flow, data_structures.
    """

    async def async_invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any] = None) -> str:
        """
        Main entry point called by the Neuro SAN framework.

        Args:
            args: Dictionary with keys:
                - source_code (str): The legacy source code to parse.
                - language (str): One of "cobol", "java", "plsql".
            sly_data: Private data channel (not used by this tool).

        Returns:
            JSON string with the parsed structure.
        """
        source_code = args.get("source_code", "")
        language = args.get("language", "").lower().strip()

        logger.info("CodeParserTool invoked for language: %s", language)

        if not source_code.strip():
            return json.dumps({"error": "No source code provided."})

        # Dispatch to the right parser based on language
        if language == "cobol":
            result = self._parse_cobol(source_code)
        elif language == "java":
            result = self._parse_java(source_code)
        elif language == "plsql":
            result = self._parse_plsql(source_code)
        else:
            return json.dumps({
                "error": f"Unsupported language: '{language}'. Supported: cobol, java, plsql."
            })

        result["language"] = language
        result["lines_of_code"] = len([
            line for line in source_code.splitlines() if line.strip()
        ])
        return json.dumps(result, indent=2)

    # -------------------------------------------------------------------------
    # COBOL Parser
    # -------------------------------------------------------------------------
    def _parse_cobol(self, code: str) -> Dict[str, Any]:
        """Parse COBOL source code to extract structure."""
        lines = code.upper()  # COBOL is case-insensitive

        # Extract DIVISION markers (e.g., IDENTIFICATION DIVISION, DATA DIVISION)
        divisions = re.findall(
            r'(\w[\w\s-]*?)\s+DIVISION',
            lines
        )

        # Extract paragraph names (lines that start with a name and end with a period)
        # In COBOL, paragraphs are entry points within a SECTION/DIVISION
        paragraphs = re.findall(
            r'^\s{0,7}(\w[\w-]+)\.\s*$',
            code,
            re.MULTILINE
        )
        # Filter out DIVISION lines that also match
        paragraphs = [
            p for p in paragraphs
            if "DIVISION" not in p.upper() and "SECTION" not in p.upper()
        ]

        # Extract WORKING-STORAGE variables (level numbers + names)
        # Pattern: level-number variable-name PIC ...
        variables = re.findall(
            r'^\s+(\d{2})\s+([\w-]+)\s+PIC\s+([^\.\n]+)',
            code,
            re.MULTILINE | re.IGNORECASE
        )
        variable_list = [
            {"level": v[0], "name": v[1], "picture": v[2].strip()}
            for v in variables
        ]

        # Extract control flow: PERFORM, IF, EVALUATE, GO TO
        performs = re.findall(r'PERFORM\s+([\w-]+)', lines)
        ifs = re.findall(r'IF\s+(.+?)(?:\s+THEN)?$', lines, re.MULTILINE)
        evaluates = re.findall(r'EVALUATE\s+(.+?)$', lines, re.MULTILINE)
        gotos = re.findall(r'GO\s+TO\s+([\w-]+)', lines)

        # Extract COMPUTE statements (business calculations)
        computes = re.findall(
            r'COMPUTE\s+([\w-]+)\s*=\s*(.+?)(?:\.|$)',
            lines,
            re.MULTILINE
        )

        # Extract MOVE statements
        moves = re.findall(
            r'MOVE\s+(.+?)\s+TO\s+([\w-]+)',
            lines,
            re.MULTILINE
        )

        return {
            "functions": paragraphs,
            "variables": variable_list,
            "control_flow": {
                "perform_calls": performs,
                "if_conditions": [i.strip() for i in ifs[:20]],
                "evaluate_blocks": [e.strip() for e in evaluates],
                "goto_statements": gotos,
            },
            "data_structures": {
                "divisions": divisions,
                "compute_statements": [
                    {"target": c[0], "expression": c[1].strip()}
                    for c in computes
                ],
                "move_statements": [
                    {"source": m[0].strip(), "target": m[1]}
                    for m in moves[:20]
                ],
            },
        }

    # -------------------------------------------------------------------------
    # Java Parser
    # -------------------------------------------------------------------------
    def _parse_java(self, code: str) -> Dict[str, Any]:
        """Parse legacy Java source code to extract structure."""

        # Extract class declarations
        classes = re.findall(
            r'(?:public|private|protected)?\s*(?:abstract|final)?\s*class\s+(\w+)',
            code
        )

        # Extract method signatures
        methods = re.findall(
            r'(?:public|private|protected)\s+(?:static\s+)?(\w+)\s+(\w+)\s*\(([^)]*)\)',
            code
        )
        method_list = [
            {"return_type": m[0], "name": m[1], "parameters": m[2].strip()}
            for m in methods
        ]

        # Extract variable declarations (field-level and local)
        variables = re.findall(
            r'(?:private|protected|public|final|static)\s+(\w+)\s+(\w+)\s*[=;]',
            code
        )
        variable_list = [
            {"type": v[0], "name": v[1]}
            for v in variables
        ]

        # Extract control flow
        ifs = re.findall(r'if\s*\((.+?)\)', code)
        switches = re.findall(r'switch\s*\((.+?)\)', code)
        for_loops = re.findall(r'for\s*\((.+?)\)', code)
        while_loops = re.findall(r'while\s*\((.+?)\)', code)
        try_catches = re.findall(r'catch\s*\((.+?)\)', code)

        # Extract method calls
        method_calls = re.findall(r'(\w+)\s*\.\s*(\w+)\s*\(', code)
        call_list = [
            f"{mc[0]}.{mc[1]}()" for mc in method_calls
        ]

        return {
            "functions": [m["name"] for m in method_list],
            "classes": classes,
            "methods": method_list,
            "variables": variable_list,
            "control_flow": {
                "if_conditions": ifs[:20],
                "switch_blocks": switches,
                "for_loops": for_loops[:10],
                "while_loops": while_loops[:10],
                "try_catch_blocks": try_catches,
            },
            "data_structures": {
                "method_calls": list(set(call_list))[:30],
            },
        }

    # -------------------------------------------------------------------------
    # PL/SQL Parser
    # -------------------------------------------------------------------------
    def _parse_plsql(self, code: str) -> Dict[str, Any]:
        """Parse PL/SQL source code to extract structure."""
        upper_code = code.upper()

        # Extract procedures and functions
        procedures = re.findall(
            r'(?:CREATE\s+(?:OR\s+REPLACE\s+)?)?PROCEDURE\s+(\w+)',
            upper_code
        )
        functions = re.findall(
            r'(?:CREATE\s+(?:OR\s+REPLACE\s+)?)?FUNCTION\s+(\w+)',
            upper_code
        )

        # Extract variable declarations
        variables = re.findall(
            r'(\w+)\s+(\w+(?:\(\d+(?:,\s*\d+)?\))?)\s*(?::=|;)',
            code,
            re.IGNORECASE
        )
        variable_list = [
            {"name": v[0], "type": v[1]}
            for v in variables
            if v[0].upper() not in ("BEGIN", "END", "IF", "THEN", "ELSE", "LOOP")
        ]

        # Extract cursors
        cursors = re.findall(
            r'CURSOR\s+(\w+)\s+IS',
            upper_code
        )

        # Extract control flow
        ifs = re.findall(r'IF\s+(.+?)\s+THEN', upper_code)
        cases = re.findall(r'CASE\s+(.+?)$', upper_code, re.MULTILINE)
        loops = re.findall(r'(FOR|WHILE)\s+(.+?)\s+LOOP', upper_code)

        return {
            "functions": procedures + functions,
            "variables": variable_list,
            "control_flow": {
                "if_conditions": [i.strip() for i in ifs[:20]],
                "case_blocks": [c.strip() for c in cases],
                "loops": [
                    {"type": lp[0], "condition": lp[1].strip()}
                    for lp in loops
                ],
            },
            "data_structures": {
                "cursors": cursors,
                "procedures": procedures,
                "standalone_functions": functions,
            },
        }
