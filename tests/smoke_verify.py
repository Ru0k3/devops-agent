from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from agent.graph import run_incident
from tools.seed_data import ALERTS

p = run_incident(ALERTS["payment-regression"], log_dir="logs/smoke")
a = run_incident(ALERTS["auth-risky"], log_dir="logs/smoke")
assert p.route == "auto-deploy" and p.deployment["production_touched"] is False
assert a.route == "escalate" and a.deployment["deployed"] is False
assert "abc1234" in p.diagnosis["citations"] and "deadbee" in a.diagnosis["citations"]
assert Path(p.report["trace_path"]).exists() and Path(a.report["trace_path"]).exists()
print("smoke verification passed")
