import json
import subprocess


def run_cmd_list(cmd_list):
    """
    Windows-safe subprocess execution using argument list.
    """
    result = subprocess.run(cmd_list, capture_output=True, text=True)
    return result.stdout.strip(), result.stderr.strip(), result.returncode


def get_owner_deployment_from_pod(pod_name: str, namespace: str = "autofix-demo"):
    """
    Pod -> ReplicaSet -> Deployment
    """
    # 1) Get pod JSON
    cmd = [
        "kubectl", "get", "pod", pod_name,
        "-n", namespace,
        "-o", "json"
    ]
    stdout, stderr, rc = run_cmd_list(cmd)

    if rc != 0:
        return None, f"Failed to get pod JSON: {stderr}"

    try:
        pod = json.loads(stdout)
        owner_refs = pod.get("metadata", {}).get("ownerReferences", [])
        rs_name = None

        for ref in owner_refs:
            if ref.get("kind") == "ReplicaSet":
                rs_name = ref.get("name")
                break

        if not rs_name:
            return None, "Pod is not owned by a ReplicaSet"
    except Exception as e:
        return None, f"Failed to parse pod JSON: {e}"

    # 2) Get ReplicaSet JSON
    cmd = [
        "kubectl", "get", "rs", rs_name,
        "-n", namespace,
        "-o", "json"
    ]
    stdout, stderr, rc = run_cmd_list(cmd)

    if rc != 0:
        return None, f"Failed to get ReplicaSet JSON: {stderr}"

    try:
        rs = json.loads(stdout)
        owner_refs = rs.get("metadata", {}).get("ownerReferences", [])

        for ref in owner_refs:
            if ref.get("kind") == "Deployment":
                return ref.get("name"), None

        return None, "ReplicaSet is not owned by a Deployment"
    except Exception as e:
        return None, f"Failed to parse ReplicaSet JSON: {e}"


def inject_env_var(deployment_name: str, env_name: str, env_value: str, namespace: str = "autofix-demo"):
    """
    BEST WAY for env injection:
    kubectl set env deployment/<name> KEY=VALUE
    This is rollout-safe and Windows-safe.
    """
    cmd = [
        "kubectl", "set", "env",
        f"deployment/{deployment_name}",
        f"{env_name}={env_value}",
        "-n", namespace
    ]

    stdout, stderr, rc = run_cmd_list(cmd)

    return {
        "success": rc == 0,
        "command": " ".join(cmd),
        "stdout": stdout,
        "stderr": stderr,
        "returncode": rc
    }


def rollout_status(deployment_name: str, namespace: str = "autofix-demo", timeout_seconds: int = 90):
    """
    Wait for deployment rollout to complete.
    """
    cmd = [
        "kubectl", "rollout", "status",
        f"deployment/{deployment_name}",
        "-n", namespace,
        f"--timeout={timeout_seconds}s"
    ]

    stdout, stderr, rc = run_cmd_list(cmd)

    return {
        "success": rc == 0,
        "command": " ".join(cmd),
        "stdout": stdout,
        "stderr": stderr,
        "returncode": rc
    }


def execute_fix(pod_name: str, recommendation: dict, namespace: str = "autofix-demo"):
    action = recommendation.get("recommended_action")

    print(f"[EXECUTOR] Resolving deployment owner for pod: {pod_name}")
    deployment_name, error = get_owner_deployment_from_pod(pod_name, namespace)

    if error:
        return {
            "success": False,
            "action": action,
            "pod_name": pod_name,
            "error": error
        }

    print(f"[EXECUTOR] Target deployment: {deployment_name}")
    print(f"[EXECUTOR] Applying action: {action}")

    if action == "inject_env":
        env_name = recommendation.get("env_name")
        env_value = recommendation.get("env_value")

        if not env_name or env_value is None:
            return {
                "success": False,
                "action": action,
                "pod_name": pod_name,
                "deployment_name": deployment_name,
                "error": "Missing env_name or env_value in recommendation"
            }

        apply_result = inject_env_var(deployment_name, env_name, env_value, namespace)

        # If apply failed, return immediately
        if not apply_result["success"]:
            return {
                "success": False,
                "action": action,
                "pod_name": pod_name,
                "deployment_name": deployment_name,
                "apply_result": apply_result
            }

        # Wait for rollout
        rollout_result = rollout_status(deployment_name, namespace, timeout_seconds=90)

        return {
            "success": rollout_result["success"],
            "action": action,
            "pod_name": pod_name,
            "deployment_name": deployment_name,
            "apply_result": apply_result,
            "rollout_result": rollout_result
        }

    elif action == "suggest_rollback":
        return {
            "success": False,
            "action": action,
            "pod_name": pod_name,
            "deployment_name": deployment_name,
            "message": "Rollback requires manual approval / CI-CD integration"
        }

    return {
        "success": False,
        "action": action,
        "pod_name": pod_name,
        "deployment_name": deployment_name,
        "error": f"Unsupported action: {action}"
    }