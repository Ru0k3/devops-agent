# Stack reference for the judges

This project follows the bootcamp capstone pattern: **retrieve evidence, assemble a constrained reasoning prompt, generate an explanation, score safety deterministically, route through a guardrail, and trace the run**.

## LangGraph

`agent/graph.py` builds and compiles a real `langgraph.graph.StateGraph`. The nodes are `alert_intake`, `log_analyzer`, `commit_correlator`, `grounded_diagnosis`, `patch_writer`, `safety_critic`, `router`, `deployer`, `escalate_to_oncall`, and `reporter`. The router uses `add_conditional_edges`; it is not a model-generated decision.

## LangChain

`agent/llm.py` uses `langchain_core.prompts.ChatPromptTemplate` to render the system and evidence messages passed to NVIDIA NIM. This keeps prompt construction separate from orchestration, matching the bootcamp's retrieve/assemble/generate separation. If LangChain is unavailable during a minimal import, the function has a small compatibility fallback.

## FastMCP

`tools/mcp_tools.py` defines seven `@mcp.tool` functions. `tools/mcp_server.py` starts a real FastMCP stdio server. The MCP smoke test discovers all seven tools and calls `fetch_logs`. The graph uses the same decorated tool boundary for the deterministic local run; the standalone server is available for an external MCP client.

## Vector database / RAG

`rag/ingest.py` creates a persistent Chroma collection named `incident-postmortems` at `rag/chroma_db/`. It embeds eight postmortems, queries cosine similarity, and returns retrieved chunks. `grounded_diagnosis` includes the retrieved IDs and suspect commit SHA in every diagnosis. Embedding priority is NVIDIA NIM, local sentence-transformers, then an offline deterministic vector fallback.

## Langfuse

`agent/observability.py` emits node spans when Langfuse keys are present. The local JSON tracer remains active in every run. The dashboard labels this as `REAL COMPONENTS` and shows the fallback state honestly when credentials are absent. To show a remote trace, configure `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, and `LANGFUSE_HOST`, run a scenario, and open the corresponding Langfuse trace.

## What to say in the demo

> “This is not a single prompt. LangGraph orchestrates specialized nodes. FastMCP provides the tools. Chroma retrieves the incident evidence. LangChain assembles the evidence-grounded prompt. Langfuse traces every node when configured, while the local JSON trace keeps the demo reproducible offline. The LLM writes explanations, but the deterministic safety critic alone controls deployment.”
