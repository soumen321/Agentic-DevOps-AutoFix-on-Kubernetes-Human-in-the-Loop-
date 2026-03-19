from pathlib import Path
import json
import time
from datetime import datetime

# Use local project folder instead of /tmp for Windows compatibility
APPROVAL_DIR = Path("approvals")
APPROVAL_DIR.mkdir(parents=True, exist_ok=True)


def create_approval_request(incident_id: str, recommendation: dict):
    request_file = APPROVAL_DIR / f"{incident_id}.json"

    payload = {
        "incident_id": incident_id,
        "status": "pending",
        "created_at": datetime.utcnow().isoformat() + "Z",
        "recommendation": recommendation
    }

    with open(request_file, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    print(f"[APPROVAL] Created approval request: {request_file.resolve()}")
    return request_file


def wait_for_approval(incident_id: str, timeout_seconds: int = 60):
    approved_file = APPROVAL_DIR / f"{incident_id}.approved"

    print(f"[APPROVAL] Waiting up to {timeout_seconds}s for approval: {incident_id}")
    print(f"[APPROVAL] Watching file: {approved_file.resolve()}")

    start = time.time()

    while time.time() - start < timeout_seconds:
        if approved_file.exists():
            print(f"[APPROVAL] Approved: {incident_id}")
            return True
        time.sleep(2)

    print(f"[APPROVAL] Timed out: {incident_id}")
    return False