import os
import json
import re

# Optional Gemini support (safe fallback if not installed)
try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain_core.messages import HumanMessage
    GEMINI_AVAILABLE = True
except Exception:
    GEMINI_AVAILABLE = False


def deterministic_check(logs: str, events: str):
    combined = f"{logs}\n{events}"

    if "OOMKilled" in combined or "exitCode: 137" in combined or "137" in combined:
        return {
            "classification": "OOMKilled",
            "root_cause": "Container exceeded memory limit",
            "recommended_action": "increase_memory",
            "memory_limit_mi": 256,
            "confidence": 0.98,
            "risk_level": "medium"
        }

    if "ImagePullBackOff" in combined or "ErrImagePull" in combined:
        return {
            "classification": "ImagePullBackOff",
            "root_cause": "Image tag invalid or registry auth issue",
            "recommended_action": "suggest_rollback",
            "confidence": 0.97,
            "risk_level": "high"
        }

    if "KeyError: 'STRIPE_API_KEY'" in combined or 'KeyError: "STRIPE_API_KEY"' in combined:
        return {
            "classification": "CrashLoop",
            "root_cause": "Missing STRIPE_API_KEY environment variable",
            "recommended_action": "inject_env",
            "env_name": "STRIPE_API_KEY",
            "env_value": "sk_test_demo_123",
            "confidence": 0.99,
            "risk_level": "low"
        }

    if "Liveness probe failed" in combined or "Readiness probe failed" in combined or "DeadlineExceeded" in combined:
        return {
            "classification": "DeadlineExceeded",
            "root_cause": "Probe configuration too aggressive or app startup too slow",
            "recommended_action": "increase_probe_delay",
            "initial_delay_seconds": 20,
            "confidence": 0.90,
            "risk_level": "medium"
        }

    return None


def safe_json_extract(text: str):
    try:
        return json.loads(text)
    except Exception:
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except Exception:
                pass

    return {
        "classification": "Unknown",
        "root_cause": "Failed to parse LLM response",
        "recommended_action": "manual_review",
        "confidence": 0.0,
        "risk_level": "high"
    }


def llm_fallback(logs: str, events: str):
    if not GEMINI_AVAILABLE:
        return {
            "classification": "Unknown",
            "root_cause": "Gemini package not installed",
            "recommended_action": "manual_review",
            "confidence": 0.0,
            "risk_level": "high"
        }

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return {
            "classification": "Unknown",
            "root_cause": "GEMINI_API_KEY not configured",
            "recommended_action": "manual_review",
            "confidence": 0.0,
            "risk_level": "high"
        }

    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-pro",
        google_api_key=api_key,
        temperature=0
    )

    prompt = f"""
You are a Kubernetes SRE agent.

Analyze the following failing pod logs and events.

LOGS:
{logs}

EVENTS:
{events}

Supported classes:
- CrashLoop
- OOMKilled
- ImagePullBackOff
- DeadlineExceeded
- Unknown

Return STRICT JSON ONLY with this schema:
{{
  "classification": "CrashLoop|OOMKilled|ImagePullBackOff|DeadlineExceeded|Unknown",
  "root_cause": "string",
  "recommended_action": "inject_env|increase_memory|increase_probe_delay|suggest_rollback|manual_review",
  "env_name": "optional string",
  "env_value": "optional string",
  "memory_limit_mi": "optional integer",
  "initial_delay_seconds": "optional integer",
  "confidence": "float 0.0 to 1.0",
  "risk_level": "low|medium|high"
}}
"""

    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        return safe_json_extract(response.content)
    except Exception as e:
        return {
            "classification": "Unknown",
            "root_cause": f"LLM call failed: {str(e)}",
            "recommended_action": "manual_review",
            "confidence": 0.0,
            "risk_level": "high"
        }


def run_diagnosis(logs: str, events: str):
    quick = deterministic_check(logs, events)
    if quick:
        return quick

    return llm_fallback(logs, events)