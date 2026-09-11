# SentinelOps

## A safety-gated DevOps incident-response agent

When a production service breaks, an engineer usually has to jump between alerts, logs, recent commits, old postmortems, tests, and deployment checks. SentinelOps brings those steps together in one workflow.

The idea is simple: **let the agent investigate and prepare a fix, but never let it deploy blindly**.

SentinelOps correlates the incident with logs and recent code changes, searches previous incidents for useful evidence, prepares a candidate patch, runs tests in a sandbox, and then makes one of two decisions:

- **Auto-deploy to an isolated sandbox** when the change is well-supported and low risk.
- **Escalate to a human** when tests fail, confidence is low, or the change touches a sensitive area.

This project was built for the **Trustworthy, Responsible & Secure AI** track. It is a reproducible local demonstration and does not connect to or modify production systems.

> **Safety invariant:** the demo deployer writes only to `logs/sandbox_deployments.jsonl` and reports `production_touched: false`. The final deployment decision is made by deterministic Python rules, not by the language model.

## Live demo

The complete demo shows both sides of the system:

**[Open the playable SentinelOps demo](https://ru0k3.github.io/devops-agent/demo.html)**

The recording covers:

1. **Payment regression:** the agent finds a missing defensive check, passes the sandbox tests, and deploys the patch to the isolated sandbox.
2. **Authentication regression:** the agent detects a sensitive authentication change, blocks deployment, and escalates the incident to on-call.

The source video is also available in the repository as [`devops.mp4`](devops.mp4).

## How the workflow works

```text
Alert
  ↓
Fetch logs
  ↓
Find recent commits and the relevant diff
  ↓
Retrieve similar postmortems from Chroma
  ↓
Write a grounded diagnosis
  ↓
Prepare a candidate patch
  ↓
Run sandbox tests
  ↓
Calculate confidence and blast radius
  ↓
Auto-deploy to the sandbox or escalate to a human
```

The implementation uses a real LangGraph `StateGraph` with these nodes:

```text
alert_intake → log_analyzer → commit_correlator → grounded_diagnosis
             → patch_writer → safety_critic → router
             → deployer → reporter
                              ↘ escalate_to_oncall → reporter
```

The router uses a LangGraph conditional edge. Its policy is deliberately straightforward:

```text
confidence >= 0.75
AND tests pass
AND no risk flag
```

If any part of that rule fails, the incident is escalated.

## The technology stack

Each component has a specific role in the project.

| Technology | How it is used |
|---|---|
| **LangGraph** | Runs the incident-response state machine and conditional router. |
| **LangChain** | Builds the structured prompts used for diagnosis and reporting. |
| **FastMCP** | Provides the controlled tool boundary for logs, commits, tests, deployment, and escalation. |
| **Chroma** | Stores and retrieves the synthetic incident postmortems used for grounding. |
| **NVIDIA NIM** | Optionally generates the natural-language diagnosis and report. |
| **Langfuse** | Optionally records traces for graph nodes and tool calls. |
| **Slack webhooks** | Optionally sends the final report or escalation to a Slack channel. |

If external services are unavailable, the project still runs locally. It uses deterministic fallbacks for reports, local JSON traces for observability, and seeded local adapters for incidents and operational tools.

## The two demo paths

### Safe path: `payment-regression`

The payment service reports:

```text
NullPointerException: customer.payment_method is None
```

The agent connects the failure to commit `abc1234`, retrieves relevant postmortems, prepares a fix, and runs the sandbox tests. The expected result is:

```text
AUTO-DEPLOY
Confidence: 94%
Tests: PASS
Blast radius: CLEAR
Deployment: isolated sandbox
production_touched: false
```

This demonstrates **controlled autonomy**.

### Escalation path: `auth-risky`

The authentication service reports a token-validation failure. The related change touches `auth/token.py`:

```diff
- issuer = claims.get('iss')
+ issuer = claims['iss']
```

Because this is a sensitive authentication path and the seeded tests fail, the agent blocks deployment:

```text
ESCALATE
Confidence: 40%
Tests: FAIL
Blast radius: FLAGGED
Deployment: BLOCKED
```

This demonstrates **responsible refusal**. The agent is still useful because it provides the diagnosis, commit, diff, citations, and test results to the human reviewer.

## Grounding and citations

The repository contains eight synthetic postmortems. Chroma stores them in a persistent collection named `incident-postmortems`.

For each incident, the agent retrieves related documents and includes their IDs in the diagnosis. For example, the payment path cites:

```text
pm-001 · pm-002 · abc1234
```

The citations connect the current failure to both historical evidence and the suspected commit. This makes the demo explainable and repeatable instead of relying only on the model's general knowledge.

## Observability

Every graph step records a state transition and, where applicable, the tool that was called. Local traces are written under `logs/`.

If Langfuse credentials are configured, the same execution can also be sent to Langfuse. Without those credentials, the local trace remains available, so the demo does not depend on a cloud account.

## Quick start

The project can be run without API keys.

```bash
git clone https://github.com/Ru0k3/devops-agent.git
cd devops-agent

python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
python3 rag/ingest.py
```

Run the command-line demo:

```bash
PYTHONPATH=. python3 run_demo.py --incident payment-regression
PYTHONPATH=. python3 run_demo.py --incident auth-risky
```

Run the dashboard:

```bash
python3 dashboard_server.py
```

Then open [http://127.0.0.1:8765](http://127.0.0.1:8765).

Run the tests and evaluation:

```bash
python3 -m pytest -q
PYTHONPATH=. python3 eval/run_eval.py
```

The current seeded evaluation reports:

```text
7/7 root causes correct
7/7 routing decisions correct
0 unsafe auto-deploys
```

## Optional environment variables

Copy `.env.example` to `.env`. You can leave everything blank for the local demo.

| Variable | Purpose |
|---|---|
| `NVIDIA_API_KEY` | Enables NVIDIA NIM-generated explanations and reports. |
| `NVIDIA_MODEL` | Selects the NIM chat model. |
| `NVIDIA_EMBEDDING_MODEL` | Selects the separate NIM embedding model used for retrieval. |
| `LANGFUSE_PUBLIC_KEY` | Langfuse public key. |
| `LANGFUSE_SECRET_KEY` | Langfuse secret key. |
| `LANGFUSE_HOST` | Langfuse host, normally `https://cloud.langfuse.com`. |
| `SLACK_WEBHOOK_URL` | Sends formatted incident reports to Slack. |

Do not commit `.env` or paste any of these values into screenshots or public issues.

## FastMCP server

The project also includes a standalone FastMCP server:

```bash
PYTHONPATH=. python3 tools/mcp_server.py
```

It exposes these tools:

```text
fetch_logs
list_recent_commits
get_commit_diff
sandbox_run_tests
deploy_to_sandbox
post_slack_report
escalate_to_oncall
```

The dashboard uses the same tool functions in-process for the local demo. The standalone server is available for an external MCP client.

## Repository layout

```text
agent/              LangGraph workflow, risk scoring, NIM, and Langfuse adapter
agent/risk.py       Diff- and path-based blast-radius scoring
tools/              FastMCP tools and server entrypoint
rag/                Chroma ingestion, retrieval, and postmortems
eval/               Seven-case evaluation set and results
sandbox_repo/       Seeded application used by the demo
 dashboard/         Judge-facing dashboard
 tests/              Regression and safety tests
logs/               Local traces and sandbox deployment records
docs/               Architecture diagram source
```

## Important limitation

This is a carefully controlled demonstration. The alerts, logs, commits, postmortems, tests, Slack fallback, and deployment adapter are seeded or local so that the full flow can be reproduced safely. The orchestration, retrieval, tool boundaries, tracing hooks, and safety gate are implemented components, but the project intentionally has no production credentials and cannot deploy to production.

That boundary is part of the design—not a missing feature.

## More project material

- [Setup guide](SETUP_GUIDE.md)
- [Stack reference](STACK_REFERENCE.md)
- [Dashboard guide](DASHBOARD.md)
- [Three-minute demo script](DEMO_SCRIPT.md)
- [Hackathon submission checklist](SUBMISSION_CHECKLIST.md)
- [Architecture diagram](docs/architecture.mmd)
- [Public GitHub repository](https://github.com/Ru0k3/devops-agent)
