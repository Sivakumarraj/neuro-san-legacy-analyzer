# Neuro SAN Example: Legacy Code Analyzer

> Extract business rules from legacy code (COBOL, Java, PL/SQL) and output a
> modernization-ready specification — powered by
> [Cognizant Neuro SAN](https://github.com/cognizant-ai-lab/neuro-san-studio).

[![Neuro SAN](https://img.shields.io/badge/Neuro%20SAN-Community%20Project-blue)](https://github.com/cognizant-ai-lab/neuro-san-studio)
[![Python](https://img.shields.io/badge/Python-3.10%2B-green)](https://python.org)
[![LLM](https://img.shields.io/badge/LLM-Gemini%202.5%20Flash-orange)](https://ai.google.dev)
[![License](https://img.shields.io/badge/License-MIT-lightgrey)](./LICENSE)

---

## Overview

Large enterprises run critical business logic in decades-old COBOL, Java, and
PL/SQL code. Before modernizing, they need to know **what the code actually
does** in business terms. This project automates that extraction using a
6-agent Neuro SAN network:

```
User sends legacy code
        │
        ▼
┌─────────────────────┐
│  1. Front-Man       │  (LLM orchestrator — routes work)
│     LegacyCode      │
│     Analyzer        │
└────┬───┬───┬───┬────┘
     │   │   │   │
     ▼   │   ▼   │
┌────────┐│┌─────────┐
│2.Code  │││4.Depend-│
│ Parser │││  ency   │  ← CodedTools (deterministic, no LLM)
│(Coded) │││ Mapper  │
│        │││(Coded)  │
└───┬────┘│└────┬────┘
    │     │     │
    ▼     ▼     ▼
┌────────┐ ┌─────────┐
│3.Biz   │ │5.Migra- │
│ Rule   │ │  tion   │  ← LLM agents (judgment + interpretation)
│Extract │ │  Risk   │
│ (LLM)  │ │ (LLM)   │
└───┬────┘ └────┬────┘
    │           │
    ▼           ▼
  ┌───────────────┐
  │ 6. Spec       │
  │  Generator    │  ← LLM agent (writes the final document)
  │   (LLM)       │
  └───────────────┘
        │
        ▼
  Modernization Spec
```

## Design Rationale: CodedTool vs LLM

Each agent type is chosen deliberately. Parsing and dependency tracing are
deterministic pattern-matching problems — a regex will always find
`PERFORM CALCULATE-LATE-FEE`, with zero hallucination risk. Interpretation,
risk evaluation, and document writing require natural-language understanding
and judgment — that is where LLM agents add value.

| Agent | Type | Reasoning |
|-------|------|-----------|
| **Front-Man** | LLM | Understands user intent and orchestrates the workflow |
| **Code Parser** | CodedTool | Parsing is deterministic regex — no hallucination |
| **Business Rule Extractor** | LLM | Interpreting code semantics requires NL understanding |
| **Dependency Mapper** | CodedTool | Tracing CALL/IMPORT is exact pattern matching |
| **Migration Risk Assessor** | LLM | Evaluating risk requires judgment |
| **Spec Generator** | LLM | Writing structured documents requires language ability |

## Project Structure

```
neuro-san-legacy-analyzer/
├── coded_tools/legacy_extraction/  # Python CodedTool implementations
│   ├── code_parser_tool.py         # Deterministic code structure extractor
│   └── dependency_mapper_tool.py   # Deterministic dependency tracer
├── registries/
│   ├── legacy_business_rules.hocon # 6-agent network definition
│   └── manifest.hocon              # Registers the network with Neuro SAN
├── config/
│   └── llm_config.hocon            # Gemini 2.5 Flash LLM configuration
├── sample_data/                    # Sample legacy programs
│   ├── cobol_payment.cob           # Payment processing with late fees
│   ├── cobol_inventory.cob         # Inventory management with reorder logic
│   └── java_legacy_billing.java    # Billing with JDBC, deprecated APIs
├── tests/                          # Unit tests for the CodedTools
│   ├── test_code_parser_tool.py
│   └── test_dependency_mapper_tool.py
├── .env.example                    # API key template (copy to .env)
├── .gitignore                      # Excludes .env and Python artifacts
├── LICENSE                         # MIT license
├── pyproject.toml                  # Dependencies and project metadata
└── README.md                       # This file
```

## Setup Instructions

### Prerequisites

- Python 3.10 or higher
- A Google Gemini API key ([get one here](https://aistudio.google.com/apikey))

### Step 1: Clone and Install

**Using uv (recommended):**

```bash
git clone https://github.com/Sivakumarraj/neuro-san-legacy-analyzer.git
cd neuro-san-legacy-analyzer
uv venv
uv pip install -e ".[dev]"
```

**Using pip:**

```bash
git clone https://github.com/Sivakumarraj/neuro-san-legacy-analyzer.git
cd neuro-san-legacy-analyzer
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
# source .venv/bin/activate
pip install -e ".[dev]"
```

### Step 2: Configure API Key

```bash
# Copy the template
cp .env.example .env

# Edit .env and replace the placeholder with your real key
# GOOGLE_API_KEY=your-actual-key-here
```

Set the environment variable (if not using python-dotenv auto-load):

```bash
# Windows PowerShell:
$env:GOOGLE_API_KEY="your-actual-key-here"

# macOS/Linux:
export GOOGLE_API_KEY="your-actual-key-here"
```

### Step 3: Set Neuro SAN Environment Variables

```bash
# Windows PowerShell:
$env:AGENT_MANIFEST_FILE="registries/manifest.hocon"
$env:AGENT_TOOL_PATH="coded_tools"

# macOS/Linux:
export AGENT_MANIFEST_FILE="registries/manifest.hocon"
export AGENT_TOOL_PATH="coded_tools"
```

### Step 4: Validate Configuration

```bash
ns check-config
```

This should confirm the HOCON is valid and the agent network loads correctly.

### Step 5: Run the Server

```bash
uv run ns run
```

The network serves on **port 8080** by default.

## Running the Unit Tests

The two CodedTools are deterministic (pure regex, no LLM), so they are fully
unit-tested against the bundled sample files:

```bash
uv run pytest
```

All tests should pass — they verify paragraph/method extraction, business
calculation detection, external call tracing, file I/O mapping, and error
handling for both COBOL and Java samples.

## Usage Example

Once the server is running, send a request through the Neuro SAN client or
API. Example using the COBOL payment sample:

```
Analyze this COBOL payment processing program and extract its business rules:

[paste contents of sample_data/cobol_payment.cob]

The language is cobol.
```

Expected output: a structured modernization specification containing:

- **Business rules** — late fee calculation, early payment discount, high-value check
- **Dependencies** — `CALL 'HIGHVAL01'`, `'NOTIF01'`, `'LEDGER01'`, file I/O
- **Risks** — hardcoded rates, external program coupling
- **Migration recommendations** — target architecture and priority order

## Key Concepts

- **HOCON**: Human-Optimized Config Object Notation — JSON-like but supports
  comments and multi-line strings. Used by Neuro SAN for declarative agent
  definitions.
- **CodedTool**: A Python class that extends `CodedTool` and implements
  `async_invoke`. Runs deterministic code — no LLM, no hallucination.
- **Front-Man**: The first agent in the `tools` array. Receives user input,
  has no `parameters` in its `function` block, cannot be a CodedTool.
- **sly_data**: A private data channel for passing sensitive info between
  agents without exposing it to the LLM's context. Not used in this project
  but available.
- **manifest.hocon**: Maps agent network files to `true`/`false` — tells the
  server which networks to load.

## License

[MIT](./LICENSE)
