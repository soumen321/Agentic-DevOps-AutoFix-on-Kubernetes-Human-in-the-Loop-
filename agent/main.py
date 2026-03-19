import os
import time
from dotenv import load_dotenv

from agent.observer import find_incidents, resolve_incident
from agent.policy import is_action_allowed
from agent.approval import create_approval_request, wait_for_approval
from agent.executor import execute_fix
from agent.audit import write_audit

load_dotenv()

APPROVAL_TIMEOUT_SECONDS = int(os.getenv("APPROVAL_TIMEOUT_SECONDS", "60"))
AUTO_APPLY = os.getenv("AUTO_APPLY", "false").lower() == "true"
NAMESPACE = os.getenv("NAMESPACE", "autofix-demo")
POLL_INTERVAL_SECONDS = int(os.getenv("POLL_INTERVAL_SECONDS", "15"))


def main():
    print("[AGENT] Starting Agentic DevOps AutoFix...")
    print(f"[CONFIG] Namespace={NAMESPACE}, AUTO_APPLY={AUTO_APPLY}, APPROVAL_TIMEOUT_SECONDS={APPROVAL_TIMEOUT_SECONDS}")

    while True:
        try:
            incidents = find_incidents(namespace=NAMESPACE)

            if not incidents:
                print("[AGENT] No incidents found.")
            else:
                for incident in incidents:
                    incident_id = incident["incident_id"]
                    pod_name = incident["pod_name"]
                    issue = incident["issue"]
                    recommendation = incident["recommendation"]

                    print(f"\n[INCIDENT] ID: {incident_id}")
                    print(f"[INCIDENT] Pod: {pod_name}")
                    print(f"[ISSUE] {issue}")
                    print(f"[RECOMMENDATION] {recommendation}")

                    allowed = is_action_allowed(recommendation)

                    audit_record = {
                        "incident_id": incident_id,
                        "pod_name": pod_name,
                        "issue": issue,
                        "recommendation": recommendation,
                        "allowed_by_policy": allowed
                    }

                    # -------------------------------------------------
                    # POLICY BLOCK
                    # -------------------------------------------------
                    if not allowed:
                        print("[POLICY] Action blocked or requires manual review.")
                        audit_record["status"] = "blocked"
                        write_audit(audit_record)

                        # Optional: resolve to avoid infinite duplicate loops in demo mode
                        resolve_incident(pod_name)
                        continue

                    # -------------------------------------------------
                    # AUTO APPLY MODE
                    # -------------------------------------------------
                    if AUTO_APPLY:
                        print("[MODE] AUTO_APPLY enabled. Executing fix directly.")
                        result = execute_fix(pod_name, recommendation)

                        audit_record["status"] = "auto_applied"
                        audit_record["execution_result"] = result
                        write_audit(audit_record)

                        # Mark this pod incident as resolved
                        resolve_incident(pod_name)
                        continue

                    # -------------------------------------------------
                    # MANUAL APPROVAL MODE
                    # -------------------------------------------------
                    create_approval_request(incident_id, recommendation)

                    approved = wait_for_approval(
                        incident_id=incident_id,
                        timeout_seconds=APPROVAL_TIMEOUT_SECONDS
                    )

                    if approved:
                        print(f"[APPROVAL] Approved: {incident_id}")
                        result = execute_fix(pod_name, recommendation)

                        audit_record["execution_result"] = result

                        if result.get("success"):
                            audit_record["status"] = "approved_and_applied"
                            print(f"[AGENT] Fix applied successfully for pod {pod_name}. Waiting for observer to auto-clear when pod recovers.")
                        else:
                            audit_record["status"] = "approved_but_fix_failed"
                            print(f"[AGENT] Fix execution failed for pod {pod_name}: {result}")

                        write_audit(audit_record)
                    else:
                        print(f"[APPROVAL] Timed out: {incident_id}")
                        audit_record["status"] = "approval_timeout"
                        write_audit(audit_record)

                        # Optional for demo:
                        # resolve timed-out incident so it doesn't stay "active" forever.
                        # If you want re-alerting, comment this out.
                        resolve_incident(pod_name)

        except Exception as e:
            print(f"[ERROR] Agent loop failed: {e}")

        time.sleep(POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()