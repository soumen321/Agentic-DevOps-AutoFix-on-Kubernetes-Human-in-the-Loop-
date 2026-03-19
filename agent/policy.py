ALLOWED_ENV_KEYS = {"STRIPE_API_KEY"}
MAX_MEMORY_LIMIT_MI = 512
MAX_PROBE_DELAY_SECONDS = 30

def is_action_allowed(recommendation: dict):
    action = recommendation.get("recommended_action")

    if action == "inject_env":
        return recommendation.get("env_name") in ALLOWED_ENV_KEYS

    if action == "increase_memory":
        requested = int(recommendation.get("memory_limit_mi", 0))
        return 0 < requested <= MAX_MEMORY_LIMIT_MI

    if action == "increase_probe_delay":
        requested = int(recommendation.get("initial_delay_seconds", 0))
        return 0 < requested <= MAX_PROBE_DELAY_SECONDS

    if action == "suggest_rollback":
        # Recommend only, never auto-apply in V1
        return False

    if action == "manual_review":
        return False

    return False