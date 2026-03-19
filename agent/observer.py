import os
import json
import subprocess
from datetime import datetime

STATE_DIR = "state"
STATE_FILE = os.path.join(STATE_DIR, "active_incidents.json")

os.makedirs(STATE_DIR, exist_ok=True)


def run_cmd(cmd: str):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout.strip(), result.stderr.strip(), result.returncode


def load_state():
    if not os.path.exists(STATE_FILE):
        return {}

    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_state(state: dict):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def generate_incident_id():
    return f"incident-{datetime.now().strftime('%Y%m%d%H%M%S')}"


def analyze_pod_issue(pod_name: str, namespace: str = "autofix-demo"):
    """
    Inspect pod logs / status and return a recommendation.
    For demo: if logs contain STRIPE_API_KEY error => inject env.
    """
    cmd = f"kubectl logs {pod_name} -n {namespace} --tail=50"
    stdout, stderr, rc = run_cmd(cmd)

    logs = stdout if rc == 0 else stderr

    # Demo rule 1: missing env var
    if "STRIPE_API_KEY" in logs or "Missing STRIPE_API_KEY" in logs:
        return {
            "classification": "CrashLoop",
            "root_cause": "Missing STRIPE_API_KEY environment variable",
            "recommended_action": "inject_env",
            "env_name": "STRIPE_API_KEY",
            "env_value": "sk_test_demo_123",
            "confidence": 0.99,
            "risk_level": "low"
        }

    # Demo fallback
    return {
        "classification": "CrashLoop",
        "root_cause": "Unknown crash reason",
        "recommended_action": "suggest_rollback",
        "confidence": 0.5,
        "risk_level": "medium"
    }


def get_crashloop_pods(namespace: str = "autofix-demo"):
    cmd = f"kubectl get pods -n {namespace} -o json"
    stdout, stderr, rc = run_cmd(cmd)

    if rc != 0:
        print(f"[OBSERVER] Failed to get pods: {stderr}")
        return []

    try:
        data = json.loads(stdout)
    except Exception as e:
        print(f"[OBSERVER] Failed to parse pod JSON: {e}")
        return []

    crashloop_pods = []

    for item in data.get("items", []):
        pod_name = item.get("metadata", {}).get("name")
        statuses = item.get("status", {}).get("containerStatuses", [])

        for cs in statuses:
            waiting = cs.get("state", {}).get("waiting")
            if waiting and waiting.get("reason") == "CrashLoopBackOff":
                crashloop_pods.append(pod_name)
                break

    return crashloop_pods


def find_incidents(namespace: str = "autofix-demo"):
    """
    Return ONLY NEW incidents.
    Prevent duplicate incident creation for the same active pod.
    """
    state = load_state()
    crashloop_pods = get_crashloop_pods(namespace)

    incidents = []

    # Clean up state for pods that are no longer crashing
    current_pods_set = set(crashloop_pods)
    changed = False

    for pod_name in list(state.keys()):
        if pod_name not in current_pods_set:
            # Pod recovered or disappeared
            state.pop(pod_name, None)
            changed = True

    # Create incidents only for new crashing pods
    for pod_name in crashloop_pods:
        if pod_name in state and state[pod_name].get("status") == "active":
            # already being handled, skip duplicate
            continue

        recommendation = analyze_pod_issue(pod_name, namespace)
        incident_id = generate_incident_id()

        incident = {
            "incident_id": incident_id,
            "pod_name": pod_name,
            "issue": "CrashLoopBackOff",
            "recommendation": recommendation
        }
        incidents.append(incident)

        state[pod_name] = {
            "incident_id": incident_id,
            "status": "active",
            "created_at": datetime.now().isoformat()
        }
        changed = True

    if changed:
        save_state(state)

    return incidents


def resolve_incident(pod_name: str):
    """
    Mark incident resolved by removing it from active state.
    This prevents duplicate re-alerting for the same old pod instance.
    If the pod is recreated with a new name and still crashes, it will be a new incident.
    """
    state = load_state()

    if pod_name in state:
        print(f"[OBSERVER] Resolving incident for pod: {pod_name}")
        state.pop(pod_name, None)
        save_state(state)
    else:
        print(f"[OBSERVER] No active incident found for pod: {pod_name}")