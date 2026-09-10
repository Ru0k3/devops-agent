from __future__ import annotations
from datetime import datetime, timezone
from uuid import uuid4
from typing import Any, TypedDict

try:
    from langgraph.graph import StateGraph, START, END
except ImportError:
    StateGraph = None
    START = "__start__"; END = "__end__"

from .state import IncidentState, Tracer
from .risk import score_safety
from .llm import generate_explanation
from .observability import node_span
from tools.mcp_tools import fetch_logs, list_recent_commits, get_commit_diff, sandbox_run_tests, deploy_to_sandbox, post_slack_report, escalate_to_oncall
from rag.ingest import retrieve


class IncidentGraphState(TypedDict, total=False):
    alert: dict[str, Any]
    severity: str
    service: str
    logs: list[dict[str, Any]]
    failure_signature: dict[str, Any]
    commits: list[dict[str, Any]]
    diagnosis: dict[str, Any]
    patch: dict[str, Any]
    test_result: dict[str, Any]
    safety: dict[str, Any]
    route: str
    deployment: dict[str, Any]
    report: dict[str, Any]
    trace_id: str
    _tracer: Any


def _record(state, node, before, after, tool=None):
    state["_tracer"].record(node, before, after, tool)
    node_span(node, before, after)
    return state


def alert_intake(state):
    state["severity"] = state["alert"].get("severity", "medium"); state["service"] = state["alert"].get("service", "unknown")
    return _record(state, "alert_intake", state["alert"], {"severity": state["severity"], "service": state["service"]})


def log_analyzer(state):
    state["logs"] = fetch_logs(state["service"], state["alert"].get("time_range", "last_15m"))
    first = state["logs"][0] if state["logs"] else {}
    state["failure_signature"] = {"exception": first.get("message", "unknown"), "endpoint": first.get("endpoint"), "stack": first.get("stack")}
    return _record(state, "log_analyzer", {"service": state["service"]}, state["failure_signature"], "fetch_logs")


def commit_correlator(state):
    state["commits"] = list_recent_commits("seeded-demo", state["service"])
    return _record(state, "commit_correlator", {"service": state["service"]}, state["commits"], "list_recent_commits")


def grounded_diagnosis(state):
    query = f"{state['service']} {state['failure_signature'].get('exception', '')} {state['failure_signature'].get('stack', '')}"
    evidence = retrieve(query)
    suspect = state["commits"][0] if state["commits"] else {}
    fallback = f"Root cause is likely commit {suspect.get('sha', 'unknown')} ({suspect.get('message', 'unknown')}). Evidence is grounded in postmortems {', '.join(d['id'] for d in evidence)} and the commit diff."
    explanation, provider = generate_explanation("You explain incidents using only supplied evidence and must cite IDs/SHA.", json_text({"logs": state["logs"], "commit": suspect, "evidence": evidence}), fallback)
    state["diagnosis"] = {"root_cause": suspect.get("message", "unknown"), "commit_sha": suspect.get("sha"), "citations": [d["id"] for d in evidence] + ([suspect["sha"]] if suspect.get("sha") else []), "evidence": evidence, "explanation": explanation, "llm_provider": provider}
    return _record(state, "grounded_diagnosis", {"query": query}, state["diagnosis"])


def patch_writer(state):
    sha = state["diagnosis"].get("commit_sha"); diff = get_commit_diff(sha) if sha else {}
    expected = {"payment-service": "restore_null_guard", "cache-service": "restore_cache_version", "inventory-service": "preserve_cursor_retry", "auth-service": "review_auth_change", "billing-service": "review_sensitive_path", "search-service": "review_oversized_diff", "notification-service": "fix_failed_tests"}.get(state["service"], "unknown")
    state["patch"] = {"sha": sha, "path": diff.get("path"), "diff": diff.get("diff", ""), "risk": diff.get("risk", "high"), "expected_fix": expected}
    state["test_result"] = sandbox_run_tests(state["patch"])
    return _record(state, "patch_writer", {"sha": sha}, {"patch": state["patch"], "tests": state["test_result"]}, "sandbox_run_tests")


def safety_critic(state):
    state["safety"] = score_safety(state["diagnosis"], state["patch"], state["test_result"])
    return _record(state, "safety_critic", {"diagnosis": state["diagnosis"], "tests": state["test_result"]}, state["safety"])


def router(state):
    safe = state["safety"]["confidence"] >= 0.75 and state["test_result"].get("passed") and not state["safety"]["risk_flag"]
    state["route"] = "auto-deploy" if safe else "escalate"
    return _record(state, "router", state["safety"], {"route": state["route"], "threshold": 0.75, "reason": "confidence >= 0.75 AND tests green AND no data-driven risk flag"})


def route_next(state):
    return "deployer" if state["route"] == "auto-deploy" else "escalate_to_oncall"


def deployer(state):
    state["deployment"] = deploy_to_sandbox(state["patch"])
    return _record(state, "deployer", state["patch"], state["deployment"], "deploy_to_sandbox")


def escalate_node(state):
    state["deployment"] = {"deployed": False, "reason": "router blocked deployment"}
    payload = build_payload(state)
    state["report"] = escalate_to_oncall(payload)
    return _record(state, "escalate_to_oncall", payload, state["report"], "escalate_to_oncall")


def reporter(state):
    payload = build_payload(state)
    explanation, provider = generate_explanation("Write a concise incident report using only supplied evidence. Do not make deployment decisions.", json_text(payload), fallback_report(state))
    payload["natural_language_report"] = explanation; payload["llm_provider"] = provider
    if state["route"] == "auto-deploy":
        state["report"] = {**post_slack_report(payload), "natural_language_report": explanation, "llm_provider": provider}
    else:
        state["report"] = {**state.get("report", {}), "natural_language_report": explanation, "llm_provider": provider}
    return _record(state, "reporter", payload, state["report"], "post_slack_report" if state["route"] == "auto-deploy" else None)


def build_payload(state):
    return {"incident": state["alert"].get("id"), "service": state["service"], "what_broke": state["failure_signature"], "why": state["diagnosis"], "confidence": state["safety"].get("confidence"), "outcome": state["route"], "patch": state["patch"], "deployment": state.get("deployment", {"deployed": False})}


def fallback_report(state):
    return f"Incident {state['alert'].get('id')} on {state['service']} routed to {state['route']} with confidence {state['safety'].get('confidence')}. Citations: {', '.join(state['diagnosis'].get('citations', []))}."


def json_text(value):
    import json
    return json.dumps(value, default=str)


def build_graph():
    if StateGraph is None: raise RuntimeError("langgraph is required; install requirements.txt")
    graph = StateGraph(IncidentGraphState)
    for name, fn in [("alert_intake", alert_intake), ("log_analyzer", log_analyzer), ("commit_correlator", commit_correlator), ("grounded_diagnosis", grounded_diagnosis), ("patch_writer", patch_writer), ("safety_critic", safety_critic), ("router", router), ("deployer", deployer), ("escalate_to_oncall", escalate_node), ("reporter", reporter)]: graph.add_node(name, fn)
    graph.add_edge(START, "alert_intake"); graph.add_edge("alert_intake", "log_analyzer"); graph.add_edge("log_analyzer", "commit_correlator"); graph.add_edge("commit_correlator", "grounded_diagnosis"); graph.add_edge("grounded_diagnosis", "patch_writer"); graph.add_edge("patch_writer", "safety_critic"); graph.add_edge("safety_critic", "router")
    graph.add_conditional_edges("router", route_next, {"deployer": "deployer", "escalate_to_oncall": "escalate_to_oncall"})
    graph.add_edge("deployer", "reporter"); graph.add_edge("escalate_to_oncall", "reporter"); graph.add_edge("reporter", END)
    return graph.compile()


COMPILED_GRAPH = None

def run_incident(alert: dict[str, Any], log_dir: str = "logs") -> IncidentState:
    global COMPILED_GRAPH
    if COMPILED_GRAPH is None: COMPILED_GRAPH = build_graph()
    trace_id = f"trace-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{uuid4().hex[:6]}"
    tracer = Tracer(log_dir)
    initial = {"alert": alert, "severity": "unknown", "service": "unknown", "logs": [], "failure_signature": {}, "commits": [], "diagnosis": {}, "patch": {}, "test_result": {}, "safety": {}, "route": "pending", "deployment": {}, "report": {}, "trace_id": trace_id, "_tracer": tracer}
    result = COMPILED_GRAPH.invoke(initial)
    path = tracer.save(trace_id, {"route": result["route"], "safety": result["safety"]})
    result["report"]["trace_path"] = str(path)
    return IncidentState(**{k: result.get(k) for k in IncidentState.__dataclass_fields__})
