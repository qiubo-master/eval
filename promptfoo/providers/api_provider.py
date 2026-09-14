import json
import urllib.error
import urllib.request


def call_api(prompt, options, context):
    config = options.get("config", {})
    base_url = config.get("apiBaseUrl", "http://localhost:8000")
    payload = json.dumps({
        "user_id": "promptfoo-redteam",
        "session_id": context.get("test", {}).get("metadata", {}).get("session_id", "redteam"),
        "message": prompt,
        "scenario": "operations_agent",
        "contexts": [],
    }).encode()
    request = urllib.request.Request(
        f"{base_url}/v1/chat",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            body = json.loads(response.read())
        return {"output": body["answer"], "metadata": {"trace_id": body["trace_id"]}}
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, KeyError) as exc:
        return {"error": str(exc)}
