import subprocess
import json
import os

NAMESPACE = os.getenv("NAMESPACE", "autofix-demo")

def run_cmd(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode, result.stdout.strip(), result.stderr.strip()

def get_pods(namespace=NAMESPACE):
    code, out, err = run_cmd(["kubectl", "get", "pods", "-n", namespace, "-o", "json"])
    if code != 0:
        raise Exception(f"Failed to get pods: {err}")
    return json.loads(out)

def get_pod_logs(pod_name, namespace=NAMESPACE, tail_lines=100):
    code, out, err = run_cmd([
        "kubectl", "logs", pod_name,
        "-n", namespace,
        "--tail", str(tail_lines)
    ])
    if code != 0:
        return err
    return out

def get_pod_events(pod_name, namespace=NAMESPACE):
    code, out, err = run_cmd([
        "kubectl", "get", "events",
        "-n", namespace,
        "--sort-by=.metadata.creationTimestamp"
    ])
    if code != 0:
        return err

    # Simple filtering by pod name
    filtered = []
    for line in out.splitlines():
        if pod_name in line:
            filtered.append(line)
    return "\n".join(filtered)

def patch_deployment_env(deployment_name, env_name, env_value, namespace=NAMESPACE):
    patch = {
        "spec": {
            "template": {
                "spec": {
                    "containers": [
                        {
                            "name": deployment_name,
                            "env": [
                                {
                                    "name": env_name,
                                    "value": env_value
                                }
                            ]
                        }
                    ]
                }
            }
        }
    }

    code, out, err = run_cmd([
        "kubectl", "patch", "deployment", deployment_name,
        "-n", namespace,
        "--type", "strategic",
        "-p", json.dumps(patch)
    ])
    return code, out, err

def patch_deployment_memory(deployment_name, memory_limit_mi, namespace=NAMESPACE):
    patch = {
        "spec": {
            "template": {
                "spec": {
                    "containers": [
                        {
                            "name": deployment_name,
                            "resources": {
                                "limits": {
                                    "memory": f"{memory_limit_mi}Mi"
                                }
                            }
                        }
                    ]
                }
            }
        }
    }

    code, out, err = run_cmd([
        "kubectl", "patch", "deployment", deployment_name,
        "-n", namespace,
        "--type", "strategic",
        "-p", json.dumps(patch)
    ])
    return code, out, err

def patch_probe_delay(deployment_name, initial_delay_seconds, namespace=NAMESPACE):
    patch = {
        "spec": {
            "template": {
                "spec": {
                    "containers": [
                        {
                            "name": deployment_name,
                            "livenessProbe": {
                                "initialDelaySeconds": initial_delay_seconds
                            },
                            "readinessProbe": {
                                "initialDelaySeconds": initial_delay_seconds
                            }
                        }
                    ]
                }
            }
        }
    }

    code, out, err = run_cmd([
        "kubectl", "patch", "deployment", deployment_name,
        "-n", namespace,
        "--type", "strategic",
        "-p", json.dumps(patch)
    ])
    return code, out, err

def rollout_status(deployment_name, namespace=NAMESPACE):
    return run_cmd([
        "kubectl", "rollout", "status",
        f"deployment/{deployment_name}",
        "-n", namespace,
        "--timeout=90s"
    ])