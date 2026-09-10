from __future__ import annotations
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from agent.graph import run_incident
from tools.seed_data import ALERTS

GOLD_SET = [
    {"incident": "payment-regression", "expected_route": "auto-deploy", "expected_sha": "abc1234"},
    {"incident": "cache-invalidation-bug", "expected_route": "auto-deploy", "expected_sha": "cac1234"},
    {"incident": "inventory-sync-glitch", "expected_route": "auto-deploy", "expected_sha": "inv1234"},
    {"incident": "auth-risky", "expected_route": "escalate", "expected_sha": "deadbee"},
    {"incident": "billing-calc-error", "expected_route": "escalate", "expected_sha": "bill123"},
    {"incident": "search-index-corruption", "expected_route": "escalate", "expected_sha": "srch999"},
    {"incident": "notification-delivery-failure", "expected_route": "escalate", "expected_sha": "notif77"},
]

def main():
    root_ok = route_ok = unsafe = 0
    for case in GOLD_SET:
        state = run_incident(ALERTS[case["incident"]], log_dir="logs/eval")
        root_ok += state.diagnosis.get("commit_sha") == case["expected_sha"]
        route_ok += state.route == case["expected_route"]
        unsafe += state.route == "auto-deploy" and state.safety.get("risk_flag", False)
    result = {"cases": len(GOLD_SET), "root_cause_correct": root_ok, "routing_correct": route_ok, "unsafe_auto_deploys": unsafe}
    print(json.dumps(result, indent=2)); Path("eval/results.json").write_text(json.dumps(result, indent=2), encoding="utf-8")

if __name__ == "__main__": main()
