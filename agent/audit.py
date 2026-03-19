import os
import json
from datetime import datetime

AUDIT_DIR = os.getenv("AUDIT_DIR", "audits")

def write_audit(record: dict):
    os.makedirs(AUDIT_DIR, exist_ok=True)

    ts = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    filename = os.path.join(AUDIT_DIR, f"audit-{ts}.json")

    with open(filename, "w") as f:
        json.dump(record, f, indent=2)

    print(f"[AUDIT] Wrote audit log: {filename}")