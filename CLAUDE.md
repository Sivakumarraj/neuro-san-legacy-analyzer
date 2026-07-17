# CLAUDE.md

## PR Description Standards (CTS / Cognizant Neuro SAN Community Projects)

When creating pull requests for Cognizant Neuro SAN community project submissions, write PR descriptions at senior-reviewer depth so the reviewer can understand the full project without cloning and reading every file. Reviewers will not go into the repo to analyze code line by line — the PR description must do that job.

Every PR description must include:

1. **Full Agent/Tool/Skill (ATS) Breakdown** — table listing every agent with its name, type (LLM agent vs CodedTool), role, and why that type was chosen
2. **Data Flow / Architecture** — diagram or step-by-step showing how agents connect, what calls what, and in what order
3. **CodedTool vs LLM Rationale** — for each agent, explain why it is deterministic (CodedTool) or requires judgment (LLM)
4. **Project Structure Walkthrough** — describe every directory and file, what it does, and how it connects to the rest
5. **HOCON Network Analysis** — explain the agent network definition: metadata, tools array, parameters, instructions, class references
6. **LLM Configuration** — which model, temperature, and why
7. **Test Coverage Summary** — what is tested, what test patterns are used, and coverage of edge cases
8. **Sample Data Description** — what sample files exist and what they demonstrate
9. **Setup & Runtime** — how to install, configure, and run
10. **Limitations** — honest assessment of what the project does NOT handle
