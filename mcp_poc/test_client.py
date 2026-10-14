"""End-to-end test of the SPCS FastMCP Entra Identity Broker.

Simulates Entra ID tokens / UPN headers for:
  - ceo@amusementpark.com    -> maps to MCP_POC_CEO (PARK_CEO)
  - analyst@amusementpark.com -> maps to MCP_POC_ANALYST (PARK_ANALYST)
"""

import json
import os
import sys
import time

import httpx

URL = os.environ.get(
    "MCP_URL", "https://abz2pr-tqmttqp-hw26207.snowflakecomputing.app/mcp"
)
API_KEY = os.environ.get("MCP_API_KEY", "123456")
CEO_PAT = os.environ.get("CEO_PAT", "").strip()
ANALYST_PAT = os.environ.get("ANALYST_PAT", "").strip()

if not CEO_PAT:
    print("WARNING: CEO_PAT not set. Ingress authentication may fail.")

ENTRA_PERSONAS = {
    "CEO Persona": {
        "entra_user": "ceo@amusementpark.com",
        "pat": CEO_PAT,
    },
    "Analyst Persona": {
        "entra_user": "analyst@amusementpark.com",
        "pat": ANALYST_PAT or CEO_PAT, # fallback PAT for ingress
    },
}

QUESTION = "What was ticket net revenue by park?"


def call(entra_user, pat, method, params=None, api_key=API_KEY, rid=1):
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
    }
    if pat:
        headers["Authorization"] = f'Snowflake Token="{pat}"'
    if api_key:
        headers["X-API-Key"] = api_key
    if entra_user:
        headers["X-Entra-User"] = entra_user

    body = {"jsonrpc": "2.0", "id": rid, "method": method, "params": params or {}}
    t = time.time()
    try:
        r = httpx.post(URL, headers=headers, json=body, timeout=300.0, follow_redirects=False)
        ms = int((time.time() - t) * 1000)
    except Exception as e:
        return 0, 0, f"HTTP request failed: {e}"

    if r.status_code != 200:
        return r.status_code, ms, r.text[:300]
    payload = r.text.split("data: ")[-1] if "data: " in r.text else r.text
    try:
        return r.status_code, ms, json.loads(payload.strip())
    except Exception:
        return r.status_code, ms, r.text[:300]


def tool(entra_user, pat, name, args=None):
    code, ms, res = call(entra_user, pat, "tools/call", {"name": name, "arguments": args or {}})
    if code != 200:
        return ms, f"HTTP Error {code}: {res}"
    if isinstance(res, dict) and "result" in res:
        content = res["result"].get("content", [])
        if content and isinstance(content, list):
            return ms, content[0].get("text", str(content))
        return ms, json.dumps(res["result"])
    return ms, str(res)


if __name__ == "__main__":
    print(f"Target URL: {URL}")
    print("\n== 1. Ingress & Auth Gate Tests")
    print("  a. No PAT header         ->", call(None, None, "tools/list")[0], "(expect 302/401: blocked by Snowflake ingress)")
    print("  b. Bogus PAT             ->", call(None, "bogus_token", "tools/list")[0], "(expect 401: blocked by Snowflake ingress)")
    print("  c. Valid PAT, no API-Key ->", call("ceo@amusementpark.com", CEO_PAT, "tools/list", api_key=None)[0], "(expect 401: blocked by MCP app layer)")

    print("\n== 2. Discover Tools (tools/list)")
    code, ms, res = call("ceo@amusementpark.com", CEO_PAT, "tools/list")
    if code == 200 and isinstance(res, dict) and "result" in res:
        tools = [t["name"] for t in res["result"].get("tools", [])]
        print(f"  Status {code} in {ms} ms. Registered tools: {tools}")
    else:
        print(f"  tools/list returned {code}: {res}")

    print("\n== 3. Entra ID Token Broker Execution (Code-Level Mapping & Data Governance)")
    for label, persona in ENTRA_PERSONAS.items():
        user = persona["entra_user"]
        pat = persona["pat"]
        print(f"\n======================================== {label} ({user}) ========================================")
        for name, args in [
            ("whoami", {}),
            ("get_financial_summary", {}),
            ("ask_park_insights", {"question": QUESTION}),
        ]:
            ms, text = tool(user, pat, name, args)
            print(f"\n[Tool: {name}] ({ms} ms):\n{text}")
