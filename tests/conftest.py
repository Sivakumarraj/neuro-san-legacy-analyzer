import sys
from unittest.mock import MagicMock

# Mock neuro_san before any coded_tools imports so tests can run
# without the full neuro-san-studio package installed.
neuro_san_mock = MagicMock()
neuro_san_mock.interfaces.coded_tool.CodedTool = object
sys.modules.setdefault("neuro_san", neuro_san_mock)
sys.modules.setdefault("neuro_san.interfaces", neuro_san_mock.interfaces)
sys.modules.setdefault("neuro_san.interfaces.coded_tool", neuro_san_mock.interfaces.coded_tool)
