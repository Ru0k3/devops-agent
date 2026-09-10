from __future__ import annotations

import hashlib
import os
from pathlib import Path
import requests
from tools.seed_data import POSTMORTEMS

DB_DIR = Path(__file__).parent / "chroma_db"
COLLECTION = "incident-postmortems"


_sentence_model = None


def _embedding(text: str) -> list[float]:
    """Prefer NIM embeddings, then local sentence-transformers, then offline hash vectors."""
    key = os.getenv("NVIDIA_API_KEY")
    if key:
        try:
            response = requests.post("https://integrate.api.nvidia.com/v1/embeddings", headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"}, json={"model": os.getenv("NVIDIA_EMBEDDING_MODEL", "nvidia/llama-3.2-nv-embedqa-e5-v5"), "input": [text]}, timeout=20)
            response.raise_for_status()
            return response.json()["data"][0]["embedding"]
        except Exception:
            pass
    global _sentence_model
    try:
        if _sentence_model is None:
            from sentence_transformers import SentenceTransformer
            _sentence_model = SentenceTransformer(os.getenv("LOCAL_EMBEDDING_MODEL", "all-MiniLM-L6-v2"))
        return _sentence_model.encode(text, normalize_embeddings=True).tolist()
    except Exception:
        pass
    # Deterministic emergency fallback keeps imports and offline demos usable.
    raw = hashlib.sha256(text.lower().encode()).digest()
    return [(byte / 255.0) for byte in raw[:32]]


def _client():
    import chromadb
    return chromadb.PersistentClient(path=str(DB_DIR))


def ingest(corpus_dir: str = "rag/postmortems") -> int:
    path = Path(corpus_dir); path.mkdir(parents=True, exist_ok=True)
    for doc in POSTMORTEMS:
        (path / f"{doc['id']}.md").write_text(doc["text"], encoding="utf-8")
    client = _client()
    collection = client.get_or_create_collection(COLLECTION, metadata={"hnsw:space": "cosine"})
    collection.upsert(ids=[d["id"] for d in POSTMORTEMS], documents=[d["text"] for d in POSTMORTEMS], embeddings=[_embedding(d["text"]) for d in POSTMORTEMS], metadatas=[{"source": "postmortem"} for _ in POSTMORTEMS])
    return len(POSTMORTEMS)


def retrieve(query: str, k: int = 2) -> list[dict[str, str]]:
    try:
        client = _client()
        collection = client.get_or_create_collection(COLLECTION, metadata={"hnsw:space": "cosine"})
        if collection.count() < len(POSTMORTEMS): ingest()
        result = collection.query(query_embeddings=[_embedding(query)], n_results=k)
        return [{"id": i, "text": t} for i, t in zip(result["ids"][0], result["documents"][0])]
    except Exception:
        # Chroma is required in requirements; this fallback only keeps imports usable before install.
        return [{"id": d["id"], "text": d["text"]} for d in POSTMORTEMS[:k]]


if __name__ == "__main__":
    print(f"ingested={ingest()}")
