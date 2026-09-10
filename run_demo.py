#!/usr/bin/env python3
from __future__ import annotations
import argparse
import json
from agent.graph import run_incident
from tools.seed_data import ALERTS

parser = argparse.ArgumentParser(description="Run the safe autonomous DevOps incident-response demo")
parser.add_argument("--incident", choices=sorted(ALERTS), default="payment-regression")
args = parser.parse_args()
state = run_incident(ALERTS[args.incident])
print(json.dumps({"trace_id": state.trace_id, "route": state.route, "safety": state.safety, "deployment": state.deployment, "report": state.report}, indent=2))
