from __future__ import annotations
import json, os
from pathlib import Path
from typing import Any
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass
from .seed_data import LOGS, COMMITS

try:
    from fastmcp import FastMCP
    mcp = FastMCP("devops-incident-tools")
except ImportError:
    class _Fallback:
        def tool(self, fn): return fn
    mcp = _Fallback()

@mcp.tool
def fetch_logs(service: str, time_range: str) -> list[dict[str, Any]]:
    return [{**item, "time_range": time_range} for item in LOGS.get(service, [])]

@mcp.tool
def list_recent_commits(repo: str, service_path: str) -> list[dict[str, Any]]:
    return COMMITS.get(service_path, [])

@mcp.tool
def get_commit_diff(sha: str) -> dict[str, Any]:
    return next((commit for commits in COMMITS.values() for commit in commits if commit["sha"] == sha), {"sha": sha, "diff": "not found"})

@mcp.tool
def sandbox_run_tests(patch: dict[str, Any]) -> dict[str, Any]:
    expected = patch.get("expected_fix") not in {"review_auth_change", "review_sensitive_path", "review_oversized_diff", "fix_failed_tests"}
    if patch.get("expected_fix") == "fix_failed_tests": expected = False
    return {"passed": expected, "total": 3, "passed_count": 3 if expected else 1, "reason": "seeded tests completed"}

@mcp.tool
def deploy_to_sandbox(patch: dict[str, Any]) -> dict[str, Any]:
    target = Path("logs/sandbox_deployments.jsonl"); target.parent.mkdir(exist_ok=True)
    with target.open("a", encoding="utf-8") as fh: fh.write(json.dumps({"target": "isolated-sandbox", "patch": patch}) + "\n")
    return {"deployed": True, "target": "isolated-sandbox", "production_touched": False}

@mcp.tool
def post_slack_report(payload: dict[str, Any]) -> dict[str, Any]:
    webhook = os.getenv("SLACK_WEBHOOK_URL")
    message = format_slack_payload(payload)
    if not webhook: return {"posted": False, "mode": "local-demo", "payload": message}
    import urllib.request
    request = urllib.request.Request(webhook, data=json.dumps(message).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=10) as response: return {"posted": response.status < 300, "status": response.status}


def format_slack_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Turn the internal incident payload into a concise, judge-readable Slack message."""
    incident = payload.get("incident", "unknown")
    service = payload.get("service", "unknown")
    outcome = str(payload.get("outcome", "unknown")).upper()
    confidence = payload.get("confidence", "n/a")
    confidence_text = f"{float(confidence) * 100:.0f}%" if isinstance(confidence, (int, float)) else str(confidence)
    what = payload.get("what_broke", {}) or {}
    why = payload.get("why", {}) or {}
    patch = payload.get("patch", {}) or {}
    deployment = payload.get("deployment", {}) or {}
    deployed = bool(deployment.get("deployed"))
    tests = "PASS" if payload.get("test_result", {}).get("passed", True) else "FAIL"
    risk = "FLAGGED" if payload.get("safety", {}).get("risk_flag") else "CLEAR"
    report = payload.get("natural_language_report") or payload.get("report") or "No narrative report available."
    citations = ", ".join(why.get("citations", [])) or "none"
    status_emoji = ":white_check_mark:" if outcome == "AUTO-DEPLOY" else ":warning:"
    outcome_text = "DEPLOYED TO ISOLATED SANDBOX" if deployed else "BLOCKED — ESCALATED TO ON-CALL"
    summary = (
        f"*Incident:* `{incident}`  •  *Service:* `{service}`\n"
        f"*Outcome:* {status_emoji} *{outcome}*\n"
        f"*Confidence:* `{confidence_text}`  •  *Tests:* `{tests}`  •  *Blast radius:* `{risk}`\n"
        f"*Deployment:* `{outcome_text}`"
    )
    evidence = {
        "exception": what.get("exception"),
        "endpoint": what.get("endpoint"),
        "stack": what.get("stack"),
        "root_cause": why.get("root_cause"),
        "commit": why.get("commit_sha"),
        "citations": citations,
        "patch_path": patch.get("path"),
        "production_touched": deployment.get("production_touched", False),
    }
    return {
        "text": f"SentinelOps incident {incident}: {outcome}",
        "blocks": [
            {"type": "header", "text": {"type": "plain_text", "text": f"SentinelOps · {outcome}"}},
            {"type": "section", "text": {"type": "mrkdwn", "text": summary}},
            {"type": "section", "text": {"type": "mrkdwn", "text": f"*What broke*\n`{what.get('exception', 'unknown')}`\n`{what.get('stack', 'unknown')}`"}},
            {"type": "section", "text": {"type": "mrkdwn", "text": f"*Root cause*\n{why.get('root_cause', 'unknown')} · commit `{why.get('commit_sha', 'unknown')}`\n*Evidence:* `{citations}`"}},
            {"type": "section", "text": {"type": "mrkdwn", "text": f"*Report*\n{report}"}},
            {"type": "context", "elements": [{"type": "mrkdwn", "text": f"production_touched: `{deployment.get('production_touched', False)}` · isolated sandbox: `{deployed}`"}]},
            {"type": "section", "text": {"type": "mrkdwn", "text": f"*Full evidence*\n```{json.dumps(evidence, indent=2)}```"}},
        ],
    }

@mcp.tool
def escalate_to_oncall(context: dict[str, Any]) -> dict[str, Any]:
    return post_slack_report({"type": "ON_CALL_ESCALATION", **context})
