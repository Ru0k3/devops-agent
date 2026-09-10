def charge(customer):
    # The demo's known-good fix is restoring this guard.
    if customer.get("payment_method") is None:
        return {"status": "declined"}
    return {"status": "charged"}
