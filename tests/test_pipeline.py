import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from agent.graph import run_incident, build_graph
from tools.seed_data import ALERTS

EXPECTED = {
    "payment-regression": ("auto-deploy", "abc1234"), "cache-invalidation-bug": ("auto-deploy", "cac1234"), "inventory-sync-glitch": ("auto-deploy", "inv1234"),
    "auth-risky": ("escalate", "deadbee"), "billing-calc-error": ("escalate", "bill123"), "search-index-corruption": ("escalate", "srch999"), "notification-delivery-failure": ("escalate", "notif77"),
}

def test_all_seven_expected_routes(tmp_path):
    for incident, (route, sha) in EXPECTED.items():
        state = run_incident(ALERTS[incident], log_dir=str(tmp_path / incident))
        assert state.route == route
        assert state.diagnosis["commit_sha"] == sha
        assert state.diagnosis["citations"]
        if route == "auto-deploy": assert state.deployment["production_touched"] is False
        else: assert state.deployment.get("deployed") is not True

def test_risk_reasons_are_decoupled(tmp_path):
    assert run_incident(ALERTS["billing-calc-error"], log_dir=str(tmp_path / "billing")).safety["blast_radius"]["sensitive_path"]
    assert run_incident(ALERTS["search-index-corruption"], log_dir=str(tmp_path / "search")).safety["blast_radius"]["oversized_diff"]
    notif = run_incident(ALERTS["notification-delivery-failure"], log_dir=str(tmp_path / "notif"))
    assert notif.safety["blast_radius"]["flags"] == [] and not notif.test_result["passed"]

def test_graph_is_stategraph_and_trace_contains_branches(tmp_path):
    graph = build_graph()
    assert graph is not None
    state = run_incident(ALERTS["payment-regression"], log_dir=str(tmp_path))
    text = Path(state.report["trace_path"]).read_text()
    for node in ["alert_intake", "grounded_diagnosis", "safety_critic", "router", "deployer", "reporter"]: assert node in text
