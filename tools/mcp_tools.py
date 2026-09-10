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
    if not webhook: return {"posted": False, "mode": "local-demo", "payload": payload}
    import urllib.request
    request = urllib.request.Request(webhook, data=json.dumps({"text": json.dumps(payload)}).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=10) as response: return {"posted": response.status < 300, "status": response.status}

@mcp.tool
def escalate_to_oncall(context: dict[str, Any]) -> dict[str, Any]:
    return post_slack_report({"type": "ON_CALL_ESCALATION", **context})
