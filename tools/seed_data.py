from __future__ import annotations

ALERTS = {
    "payment-regression": {"id": "inc-001", "service": "payment-service", "severity": "critical", "message": "HTTP 500 rate above 20% on /charge", "time_range": "last_15m"},
    "cache-invalidation-bug": {"id": "inc-002", "service": "cache-service", "severity": "high", "message": "Stale cache responses after release", "time_range": "last_15m"},
    "inventory-sync-glitch": {"id": "inc-003", "service": "inventory-service", "severity": "high", "message": "Inventory sync retries increased", "time_range": "last_15m"},
    "auth-risky": {"id": "inc-004", "service": "auth-service", "severity": "high", "message": "Login failures after release; auth path changed", "time_range": "last_15m"},
    "billing-calc-error": {"id": "inc-005", "service": "billing-service", "severity": "critical", "message": "Ledger totals diverge on invoice calculation", "time_range": "last_15m"},
    "search-index-corruption": {"id": "inc-006", "service": "search-service", "severity": "critical", "message": "Search index documents corrupted after bulk update", "time_range": "last_15m"},
    "notification-delivery-failure": {"id": "inc-007", "service": "notification-service", "severity": "medium", "message": "Notification delivery test failures", "time_range": "last_15m"},
}

LOGS = {
    "payment-service": [{"timestamp": "2026-09-10T09:10:00Z", "level": "ERROR", "endpoint": "/charge", "message": "NullPointerException: customer.payment_method is None", "stack": "payments/charge.py:42"}],
    "cache-service": [{"timestamp": "2026-09-10T09:10:00Z", "level": "ERROR", "endpoint": "/cache", "message": "CacheInvalidationError: version token not updated", "stack": "cache/invalidate.py:31"}],
    "inventory-service": [{"timestamp": "2026-09-10T09:10:00Z", "level": "ERROR", "endpoint": "/sync", "message": "InventorySyncError: stale cursor retry", "stack": "inventory/sync.py:55"}],
    "auth-service": [{"timestamp": "2026-09-10T09:11:00Z", "level": "ERROR", "endpoint": "/login", "message": "TokenValidationError: issuer missing", "stack": "auth/token.py:18"}],
    "billing-service": [{"timestamp": "2026-09-10T09:12:00Z", "level": "ERROR", "endpoint": "/invoice", "message": "LedgerMismatchError: calculated total differs", "stack": "billing/ledger.py:77"}],
    "search-service": [{"timestamp": "2026-09-10T09:13:00Z", "level": "ERROR", "endpoint": "/index", "message": "IndexCorruptionError: malformed document batch", "stack": "search/indexer.py:101"}],
    "notification-service": [{"timestamp": "2026-09-10T09:14:00Z", "level": "ERROR", "endpoint": "/send", "message": "DeliveryTestError: provider timeout", "stack": "notify/provider.py:12"}],
}

COMMITS = {
    "payment-service": [{"sha": "abc1234", "message": "remove defensive payment method check", "path": "payments/charge.py", "risk": "low", "diff": "- if customer.payment_method is None: return declined\n+ payment_method = customer.payment_method"}],
    "cache-service": [{"sha": "cac1234", "message": "skip cache version bump during invalidation", "path": "cache/invalidate.py", "risk": "low", "diff": "- version += 1\n+ pass"}],
    "inventory-service": [{"sha": "inv1234", "message": "change cursor retry handling", "path": "inventory/sync.py", "risk": "low", "diff": "- retry(cursor)\n+ retry(cursor, backoff=1)"}],
    "auth-service": [{"sha": "deadbee", "message": "refactor token issuer validation", "path": "auth/token.py", "risk": "high", "diff": "- issuer = claims.get('iss')\n+ issuer = claims['iss']"}],
    "billing-service": [{"sha": "bill123", "message": "adjust ledger rounding calculation", "path": "billing/ledger.py", "risk": "medium", "diff": "- total = round(total, 2)\n+ total = int(total * 100) / 100"}],
    "search-service": [{"sha": "srch999", "message": "bulk rewrite search document mapper", "path": "search/indexer.py", "risk": "low", "diff": "-" + " changed mapping line\n" + "\n".join(f"+ changed mapping line {i}" for i in range(1, 14))}],
    "notification-service": [{"sha": "notif77", "message": "switch notification provider timeout defaults", "path": "notify/provider.py", "risk": "low", "diff": "- timeout = 10\n+ timeout = 2"}],
}

POSTMORTEMS = [
    {"id": "pm-001", "text": "Payment-service NullPointerException followed removal of a null guard. Restore the defensive check. Citation: abc1234."},
    {"id": "pm-002", "text": "Cache invalidation regression occurs when the version token is not incremented. Restore the version bump. Citation: cac1234."},
    {"id": "pm-003", "text": "Inventory sync retry glitches are fixed by preserving cursor retry handling and backoff. Citation: inv1234."},
    {"id": "pm-004", "text": "Auth issuer validation changes affect authentication and require escalation when auth/token.py is touched. Citation: deadbee."},
    {"id": "pm-005", "text": "Billing ledger calculation changes are sensitive even when tests pass. Escalate any ledger path change. Citation: bill123."},
    {"id": "pm-006", "text": "Search index bulk mapping rewrites with more than ten changed lines have oversized blast radius. Escalate for review. Citation: srch999."},
    {"id": "pm-007", "text": "Notification provider timeout changes must be tested; a failed test alone requires escalation even on a safe path. Citation: notif77."},
    {"id": "pm-008", "text": "HTTP 500 and endpoint stack evidence must be cross-checked with the commit diff before a sandbox deployment."},
]
