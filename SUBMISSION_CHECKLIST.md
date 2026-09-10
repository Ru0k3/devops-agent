# Hackathon Submission Checklist

## Chosen track

**Track 03 — Trustworthy, Responsible & Secure AI.** The project is an autonomous DevOps incident-response agent whose primary differentiator is explicit confidence gating, safe sandbox-only deployment, escalation, auditability, and prompt-injection/data-care boundaries.

## Technical bar

| PDF requirement | Repository evidence | Status |
|---|---|---|
| Multi-agent orchestration | `agent/graph.py`: 10 named LangGraph nodes and conditional route | Complete |
| Tool use / MCP | `tools/mcp_server.py`, FastMCP-decorated tools, `tests/test_mcp_server.py` | Complete |
| RAG grounding | Persistent Chroma collection with eight postmortems; diagnosis cites IDs and SHAs | Complete |
| Confidence and guardrails | `agent/risk.py` and deterministic router threshold | Complete |
| Escalation / resilience | `escalate_to_oncall` branch carries logs, evidence, diff, score, and reason | Complete |
| Evaluation | Honest seven-incident gold set; expected 7/7 and zero unsafe auto-deploys | Complete |
| Observability | Langfuse adapter plus local JSON trace for every node and decision | Complete, cloud credentials optional |
| Security and data care | No production deploy target; secrets only through environment variables; untrusted evidence is not executed | Complete |
| Local-first bonus | NVIDIA and Langfuse fallbacks; deterministic offline reports and local traces | Complete |

## Toolkit mapping

The PDF lists alternatives, not a requirement to use every provider. This implementation uses one valid choice in each category:

| Toolkit category | Selected implementation |
|---|---|
| LLM inference | NVIDIA NIM, with deterministic offline fallback |
| Orchestration | LangGraph `StateGraph` |
| MCP | FastMCP |
| Vector storage | Chroma |
| Notifications | Slack webhook with local fallback |

Using every listed alternative provider simultaneously would add redundant dependencies and would not improve the rubric score. The PDF explicitly permits alternatives.

## Submission items still requiring the team

- Push the repository to a **public GitHub repository**.
- Record a **public YouTube video of at most three minutes** and add its URL to the README or submission form.
- Submit the public repository URL, video URL, chosen track, and team details through the Google Form when the organizers publish it.
