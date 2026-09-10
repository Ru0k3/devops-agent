from __future__ import annotations
import os
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    from langfuse import get_client
    _client = get_client() if os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY") else None
except Exception:
    _client = None


def node_span(name: str, input_data, output_data):
    """Emit a real Langfuse span using the current SDK; never break the local demo."""
    if not _client:
        return
    try:
        with _client.start_as_current_observation(name=name, as_type="span", input=input_data) as span:
            span.update(output=output_data)
        _client.flush()
    except Exception:
        pass


def langfuse_status() -> str:
    return "configured" if _client else "offline-fallback"
