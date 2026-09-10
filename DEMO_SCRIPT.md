# Three-Minute Demo Script

**0:00–0:20 — Problem and track.** State that the project is Track 03, Trustworthy, Responsible & Secure AI. Explain that cloud incidents require fast diagnosis without allowing an unreviewed patch to reach production.

**0:20–0:45 — Architecture.** Trigger `payment-regression`. Show the LangGraph flow from alert intake through log analysis, commit correlation, Chroma retrieval, patch testing, safety critic, conditional router, and reporter. Point out that the graph has a real conditional edge.

**0:45–1:15 — Grounding and tools.** Show the seeded error log, commit `abc1234`, the retrieved postmortem IDs, and the FastMCP tool names. Explain that the diagnosis cites the retrieved IDs and commit SHA rather than relying on model memory.

**1:15–1:45 — Safe branch.** Show the numeric confidence score, passing tests, no blast-radius flags, and the auto-deploy decision. Open the deployment result and show `target: isolated-sandbox` and `production_touched: false`.

**1:45–2:15 — Escalation branch.** Trigger `billing-calc-error` or `auth-risky`. Show that the sensitive-path flag blocks deployment even if tests pass, or that failed tests alone block the notification incident. Show that the escalation payload contains logs, diagnosis, citations, diff, confidence, and reason.

**2:15–2:40 — Observability and offline mode.** Open a local JSON trace showing each node, tool call, and router decision. Mention that Langfuse spans are emitted when credentials are configured, while local traces remain available offline. Show `llm_provider: offline-fallback` if no NVIDIA key is configured.

**2:40–3:00 — Evaluation and close.** Run `python3 eval/run_eval.py` and show `7/7` root-cause matches, `7/7` routing matches, and `0` unsafe auto-deploys. Close by repeating that the system is autonomous inside a controlled sandbox, not a production YOLO deployer.
