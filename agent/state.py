from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import json


@dataclass
class IncidentState:
    alert: dict[str, Any]
    severity: str = "unknown"
    service: str = "unknown"
    logs: list[dict[str, Any]] = field(default_factory=list)
    failure_signature: dict[str, Any] = field(default_factory=dict)
    commits: list[dict[str, Any]] = field(default_factory=list)
    diagnosis: dict[str, Any] = field(default_factory=dict)
    patch: dict[str, Any] = field(default_factory=dict)
    test_result: dict[str, Any] = field(default_factory=dict)
    safety: dict[str, Any] = field(default_factory=dict)
    route: str = "pending"
    deployment: dict[str, Any] = field(default_factory=dict)
    report: dict[str, Any] = field(default_factory=dict)
    trace_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class Tracer:
    def __init__(self, log_dir: str = "logs") -> None:
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.events: list[dict[str, Any]] = []

    def record(self, node: str, input_summary: Any, output_summary: Any, tool: str | None = None) -> None:
        self.events.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "node": node,
            "tool": tool,
            "input": input_summary,
            "output": output_summary,
        })

    def save(self, trace_id: str, decision: dict[str, Any]) -> Path:
        payload = {"trace_id": trace_id, "events": self.events, "router_decision": decision}
        path = self.log_dir / f"{trace_id}.json"
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return path
