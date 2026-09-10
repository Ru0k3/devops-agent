from __future__ import annotations
import os
import requests
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

NIM_URL = "https://integrate.api.nvidia.com/v1/chat/completions"
MODEL = os.getenv("NVIDIA_MODEL", "nvidia/nemotron-3.5-lightning-30b-a3b")
UNSAFE_OUTPUT_MARKERS = ("thinking process", "<think>", "</think>", "chain of thought", "analysis:")

try:
    from langchain_core.prompts import ChatPromptTemplate
except ImportError:
    ChatPromptTemplate = None


def render_messages(system: str, user: str) -> list[dict[str, str]]:
    """Use LangChain's prompt abstraction; retain a tiny fallback for import-light tools."""
    if ChatPromptTemplate is not None:
        prompt = ChatPromptTemplate.from_messages([("system", system), ("human", "{evidence}")])
        messages = prompt.format_messages(evidence=user)
        return [{"role": "system" if message.type == "system" else "user", "content": message.content} for message in messages]
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def generate_explanation(system: str, user: str, fallback: str) -> tuple[str, str]:
    key = os.getenv("NVIDIA_API_KEY")
    if not key:
        return fallback, "offline-fallback"
    try:
        response = requests.post(NIM_URL, headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"}, json={"model": MODEL, "messages": render_messages(system, user), "temperature": 0.1, "max_tokens": 300}, timeout=20)
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"].strip()
        if any(marker in content.lower() for marker in UNSAFE_OUTPUT_MARKERS):
            return fallback, "offline-fallback"
        return content, "nvidia-nim"
    except Exception as exc:
        return f"{fallback} (NVIDIA NIM unavailable: {type(exc).__name__})", "offline-fallback"
