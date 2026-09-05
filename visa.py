from src.chargeback.visa_ce3 import VisaCE3Engine
import json

# Initialize the engine you just built
engine = VisaCE3Engine()

# Fake a disputed transaction
disputed_txn = {
    "timestamp": "2026-09-01T10:00:00Z",
    "card_hash": "card_xyz789",
    "ip_address": "192.168.1.5",
    "device_fingerprint": "device_abc123"
}

# Fake some history
historical_txns = [
    {
        "id": "txn_1",
        "timestamp": "2026-04-04T10:00:00Z", 
        "card_hash": "card_xyz789",
        "is_disputed": False,
        "ip_address": "192.168.1.5",
        "device_fingerprint": "device_abc123"
    },
    {
        "id": "txn_2",
        "timestamp": "2026-02-13T10:00:00Z",
        "card_hash": "card_xyz789",
        "is_disputed": False,
        "ip_address": "192.168.1.5",
        "device_fingerprint": "device_abc123"
    }
]

# Run the engine!
result = engine.evaluate_ce3_eligibility(disputed_txn, historical_txns, "10.4")
print(json.dumps(result, indent=2))