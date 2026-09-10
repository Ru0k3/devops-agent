from __future__ import annotations

SENSITIVE_PATHS = ("auth/", "token", "ledger", "data/", "migration")


def changed_lines(diff: str) -> int:
    return sum(1 for line in diff.splitlines() if line.startswith(("+", "-")) and not line.startswith(("+++", "---")))


def compute_blast_radius(patch: dict) -> dict:
    path = (patch.get("path") or "").lower()
    lines = changed_lines(patch.get("diff", ""))
    sensitive = any(marker in path for marker in SENSITIVE_PATHS)
    oversized = lines > 10
    score = 0.2 if sensitive or oversized else 0.9
    flags = []
    if sensitive: flags.append("sensitive-path")
    if oversized: flags.append("oversized-diff")
    return {"score": score, "changed_lines": lines, "sensitive_path": sensitive, "oversized_diff": oversized, "flags": flags}


def score_safety(diagnosis: dict, patch: dict, tests: dict) -> dict:
    root = 0.9 if diagnosis.get("citations") else 0.2
    test_pass = 1.0 if tests.get("passed") else 0.0
    blast = compute_blast_radius(patch)
    confidence = round(root * 0.4 + test_pass * 0.4 + blast["score"] * 0.2, 2)
    return {"root_cause_confidence": root, "test_pass_rate": test_pass, "blast_radius_score": blast["score"], "confidence": confidence, "risk_flag": bool(blast["flags"]), "blast_radius": blast}
