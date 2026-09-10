# Judge Dashboard

The dashboard is a thin presentation layer over the existing agent. It does not change the architecture, safety policy, data, or routing logic.

```bash
cd devops-agent
PYTHONPATH=. python3 dashboard_server.py
```

Open <http://127.0.0.1:8765>. Click **Run safe path** to show an isolated sandbox deployment. Click **Run escalation path** to show a blocked deployment with the confidence score, risk flag, citations, diff, and trace.

The interface is intentionally optimized for the three-minute judging demo:

1. Seeded incident selector.
2. Clear route and confidence metrics.
3. Five-stage visual execution pipeline.
4. Grounded evidence citations.
5. Proposed diff and sandbox-only outcome.
6. Local trace and tool-call list.

The **Stack proof** card is specifically for the judge question “where did you use each technology?” It identifies the actual `StateGraph`, `ChatPromptTemplate`, FastMCP tools, persistent Chroma collection, and Langfuse span adapter used by the run.

The API endpoint is local-only and calls the same `run_incident()` function used by the CLI and evaluation runner.
