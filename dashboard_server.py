from __future__ import annotations
import json
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from agent.graph import run_incident
from tools.seed_data import ALERTS

ROOT = Path(__file__).parent

class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs): super().__init__(*args, directory=str(ROOT / "dashboard"), **kwargs)
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/run":
            incident = parse_qs(parsed.query).get("incident", ["payment-regression"])[0]
            if incident not in ALERTS:
                self.send_error(404, "Unknown incident"); return
            state = run_incident(ALERTS[incident], log_dir="logs/dashboard")
            trace = json.loads(Path(state.report["trace_path"]).read_text())
            payload = state.to_dict()
            payload["trace_events"] = trace.get("events", [])
            payload["stack_proof"] = {
                "LangGraph": "StateGraph nodes + conditional router edge",
                "LangChain": "ChatPromptTemplate renders diagnosis/report messages",
                "FastMCP": "fetch_logs, commit, test, deploy, report tool boundary",
                "Chroma": "persistent incident-postmortems cosine collection",
                "Langfuse": "node spans when LANGFUSE keys are configured; local trace fallback active",
            }
            payload.pop("_tracer", None)
            raw = json.dumps(payload, default=str).encode()
            self.send_response(200); self.send_header("Content-Type", "application/json"); self.send_header("Content-Length", str(len(raw))); self.end_headers(); self.wfile.write(raw); return
        if parsed.path in ("/", "/index.html"): self.path = "/index.html"
        return super().do_GET()
    def log_message(self, format, *args): pass

if __name__ == "__main__":
    port = 8765
    print(f"SentinelOps dashboard: http://127.0.0.1:{port}")
    ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()
