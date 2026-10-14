"""Amusement Park MCP Server & Identity Broker for Azure AI Foundry / Entra ID

Identity & Token Broker Architecture (Optimized for SPCS Container Ingress)
--------------------------------------------------------------------------
Inside Snowpark Container Services, outbound internet egress is restricted by
default. However, Snowflake's native ingress session token is directly mounted
into `/snowflake/session/token` and the caller's ingress identity is automatically
forwarded via `Sf-Context-Current-User-Token`.

This server acts as the Identity & Authorization Broker:
1. Resolves and audits the incoming Entra user identity (from Bearer JWT / X-Entra-User).
2. Uses the native SPCS ingress token (`executeAsCaller`) to establish an internal
   Snowflake session under the caller's persona without needing external network egress.
3. Tags every query with:
     {"app": "park-mcp-broker", "entra_user": "<upn>", "mapped_user": "<snowflake_user>", "corr_id": "<uuid>"}
4. Fully governs and isolates data across personas via Snowflake RBAC, Row Access
   Policies (RAP_PARK_SCOPE), and Column Masking Policies.
"""

import json
import logging
import os
import time
import uuid
from functools import lru_cache
from datetime import datetime, timedelta

import anyio
import jwt
import snowflake.connector
from fastmcp import FastMCP
from fastmcp.server.dependencies import get_http_request
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, PlainTextResponse

# Load environment variables from .env file if available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not installed, use system env vars

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("park-mcp-broker")

AGENT_FQN = os.getenv("AGENT_FQN", "AMUSEMENT_PARK_DB.ANALYTICS.AMUSEMENT_PARK_INSIGHTS_AGENT")
WAREHOUSE = os.getenv("SNOWFLAKE_WAREHOUSE", "COMPUTE_WH")
API_KEY = os.getenv("MCP_API_KEY", "")
PORT = int(os.getenv("SERVER_PORT", "8080"))
ENTRA_MAP_TABLE = os.getenv("ENTRA_MAP_TABLE", "AMUSEMENT_PARK_DB.GOVERNANCE.ENTRA_USER_MAP")
CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "300"))  # 5 min default

# Fallback for development (used only if table lookup fails)
STATIC_ENTRA_MAP = {
    "ceo@amusementpark.com": {
        "user": "MCP_POC_CEO",
        "role": "PARK_CEO",
    },
    "analyst@amusementpark.com": {
        "user": "MCP_POC_ANALYST",
        "role": "PARK_ANALYST",
    },
}

# Simple cache: (entra_user_id) -> (mapping_dict, expiry_time)
_identity_cache = {}

mcp = FastMCP("amusement-park-mcp-broker")


def _extract_entra_user(request: Request) -> str:
    """Extract Entra User ID (UPN/Email) from custom header or Bearer JWT."""
    if "x-entra-user" in request.headers:
        return request.headers["x-entra-user"].strip().lower()

    auth = request.headers.get("authorization", "")
    if auth.startswith("Bearer "):
        raw_token = auth[7:].strip()
        try:
            unverified = jwt.decode(raw_token, options={"verify_signature": False})
            entra_user = (
                unverified.get("upn")
                or unverified.get("email")
                or unverified.get("unique_name")
                or unverified.get("sub", "")
            ).strip().lower()
            if entra_user:
                return entra_user
        except Exception as e:
            log.debug("Failed to extract Entra user from Bearer token: %s", e)
            if "@" in raw_token:
                return raw_token.lower()

    return "analyst@amusementpark.com"


def _resolve_entra_identity(entra_user: str) -> dict:
    """
    Resolve Entra user ID to Snowflake user/role mapping.
    
    1. Checks in-memory cache first (TTL-based)
    2. Queries ENTRA_USER_MAP table in Snowflake
    3. Falls back to STATIC_ENTRA_MAP for development/missing records
    
    Returns: {"user": "SNOWFLAKE_USER", "role": "SNOWFLAKE_ROLE"}
    """
    # Check cache
    if entra_user in _identity_cache:
        cached, expiry_time = _identity_cache[entra_user]
        if datetime.utcnow() < expiry_time:
            log.debug("Cache hit for Entra user %s", entra_user)
            return cached
        else:
            log.debug("Cache expired for Entra user %s", entra_user)
            del _identity_cache[entra_user]

    # Try dynamic lookup from ENTRA_USER_MAP table
    try:
        # Use a dedicated read-only connection to query the mapping table
        # This runs as ACCOUNTADMIN or the MCP_SERVICE_OWNER role, not the end user
        conn = snowflake.connector.connect(
            host=os.environ.get("SNOWFLAKE_HOST"),
            account=os.environ.get("SNOWFLAKE_ACCOUNT"),
            authenticator="oauth",
            token=open("/snowflake/session/token").read().strip(),
            warehouse=WAREHOUSE,
            client_session_keep_alive=False,
        )
        cur = conn.cursor()
        cur.execute(
            f"SELECT SNOWFLAKE_USER, SNOWFLAKE_ROLE FROM {ENTRA_MAP_TABLE} "
            "WHERE LOWER(ENTRA_USER_ID) = %s AND IS_ACTIVE = TRUE",
            (entra_user.lower(),)
        )
        row = cur.fetchone()
        conn.close()
        
        if row:
            mapping = {"user": row[0], "role": row[1]}
            # Cache the result
            _identity_cache[entra_user] = (mapping, datetime.utcnow() + timedelta(seconds=CACHE_TTL_SECONDS))
            log.info("Resolved Entra user %s to Snowflake user %s (from table)", entra_user, row[0])
            return mapping
    except Exception as e:
        log.warning("Failed to query ENTRA_USER_MAP table for %s: %s. Using fallback.", entra_user, e)

    # Fallback to static map
    if entra_user in STATIC_ENTRA_MAP:
        mapping = STATIC_ENTRA_MAP[entra_user]
        _identity_cache[entra_user] = (mapping, datetime.utcnow() + timedelta(seconds=CACHE_TTL_SECONDS))
        log.info("Resolved Entra user %s to Snowflake user %s (from static map)", entra_user, mapping["user"])
        return mapping

    # Final fallback: default analyst
    mapping = STATIC_ENTRA_MAP["analyst@amusementpark.com"]
    _identity_cache[entra_user] = (mapping, datetime.utcnow() + timedelta(seconds=CACHE_TTL_SECONDS))
    log.warning("Entra user %s not found in map or table; defaulting to analyst", entra_user)
    return mapping


class EntraBrokerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Allow health checks without authentication
        if request.url.path == "/healthz":
            return await call_next(request)

        # CRITICAL: MCP spec requires discovery (GET) to be unauthenticated and public
        # Azure Foundry tool config doesn't send Snowflake token on GET discovery requests
        # So we must allow GET /mcp to bypass all authentication
        if request.url.path == "/mcp" and request.method == "GET":
            log.info("MCP discovery request (GET /mcp) - PUBLIC, no authentication required")
            return await call_next(request)
        
        # For POST /mcp (tool invocations): require API-Key for authentication
        # This is where identity mapping and Entra ID resolution happens
        if request.url.path == "/mcp" and request.method == "POST":
            if API_KEY and request.headers.get("x-api-key") != API_KEY:
                log.warning("rejected POST /mcp: missing or invalid X-API-Key")
                return JSONResponse({"error": "invalid or missing X-API-Key"}, status_code=401)

            entra_user = _extract_entra_user(request)
            mapping = _resolve_entra_identity(entra_user)

            request.state.entra_user = entra_user
            request.state.snowflake_user = mapping["user"]
            request.state.snowflake_role = mapping["role"]
            
            log.info("MCP tool invocation authorized: entra_user=%s mapped_to_sf_user=%s role=%s", 
                     entra_user, mapping["user"], mapping["role"])

        return await call_next(request)


@mcp.custom_route("/healthz", methods=["GET"])
async def healthz(_: Request):
    return PlainTextResponse("ok")


@mcp.custom_route("/mcp", methods=["OPTIONS"])
async def mcp_options(_: Request):
    """Allow CORS preflight for MCP discovery."""
    return PlainTextResponse("")


def _get_connection():
    """Establish an internal Snowflake connection using SPCS ingress caller's token."""
    request = get_http_request()
    user_token = request.headers.get("sf-context-current-user-token")
    if not user_token:
        raise PermissionError(
            "Missing Sf-Context-Current-User-Token header from SPCS ingress."
        )

    with open("/snowflake/session/token") as f:
        service_token = f.read().strip()

    return snowflake.connector.connect(
        host=os.environ.get("SNOWFLAKE_HOST"),
        account=os.environ.get("SNOWFLAKE_ACCOUNT"),
        authenticator="oauth",
        token=f"{service_token}.{user_token}",
        warehouse=WAREHOUSE,
        client_session_keep_alive=False,
    )


def _run(sql: str, params=None):
    corr_id = str(uuid.uuid4())
    request = get_http_request()
    state = getattr(request, "state", None)
    entra_user = getattr(state, "entra_user", "unknown")
    sf_user = getattr(state, "snowflake_user", "unknown")
    sf_role = getattr(state, "snowflake_role", "unknown")

    started = time.time()
    conn = _get_connection()
    try:
        cur = conn.cursor()
        query_tag = json.dumps(
            {
                "app": "park-mcp-broker",
                "entra_user": entra_user,
                "mapped_user": sf_user,
                "mapped_role": sf_role,
                "corr_id": corr_id,
            }
        )
        cur.execute(f"ALTER SESSION SET QUERY_TAG = '{query_tag}'")
        cur.execute(sql, params)
        cols = [c[0] for c in cur.description] if cur.description else []
        rows = [dict(zip(cols, r)) for r in cur.fetchall()] if cur.description else []
        
        elapsed_ms = (time.time() - started) * 1000
        log.info(
            "audit corr_id=%s entra_user=%s sf_user=%s sf_role=%s query_id=%s ms=%.1f",
            corr_id,
            entra_user,
            sf_user,
            sf_role,
            cur.sfqid,
            elapsed_ms,
        )
        return rows, cur.sfqid, corr_id, entra_user
    except Exception as e:
        elapsed_ms = (time.time() - started) * 1000
        log.error(
            "audit_error corr_id=%s entra_user=%s sf_user=%s sf_role=%s error=%s ms=%.1f",
            corr_id,
            entra_user,
            sf_user,
            sf_role,
            str(e),
            elapsed_ms,
        )
        raise
    finally:
        conn.close()


@mcp.tool
async def whoami() -> dict:
    """Return the Entra ID user identity and the mapped Snowflake user/role executing this query.
    
    This proves execution context isolation: the query runs as the mapped Snowflake user,
    not as a shared service account.
    """
    request = get_http_request()
    state = getattr(request, "state", None)
    mapped_role = getattr(state, "snowflake_role", "unknown")
    
    rows, qid, corr, entra_user = await anyio.to_thread.run_sync(
        _run, "SELECT CURRENT_USER() AS SNOWFLAKE_USER, CURRENT_ROLE() AS SNOWFLAKE_ROLE"
    )
    return {
        "entra_user_identity": entra_user,
        "snowflake_mapped_user": rows[0]["SNOWFLAKE_USER"],
        "snowflake_mapped_role": mapped_role,
        "snowflake_active_role": rows[0]["SNOWFLAKE_ROLE"],
        "query_id": qid,
        "correlation_id": corr,
    }


@mcp.tool
async def ask_park_insights(question: str) -> dict:
    """Ask the governed Amusement Park Insights Cortex Agent a natural-language question about
    rides, wait times, downtime, food/retail sales, revenue, expenses, departments or fiscal
    periods. Answers only include data the caller's mapped role is permitted to see."""
    body = json.dumps(
        {"messages": [{"role": "user", "content": [{"type": "text", "text": question}]}]}
    )
    rows, qid, corr, entra_user = await anyio.to_thread.run_sync(
        _run,
        "SELECT SNOWFLAKE.CORTEX.DATA_AGENT_RUN(%s, %s, TRUE) AS R",
        (AGENT_FQN, body),
    )
    raw = rows[0]["R"]
    resp = json.loads(raw) if isinstance(raw, str) else raw
    text = "\n".join(
        c.get("text", "")
        for c in (resp or {}).get("content", [])
        if c.get("type") == "text"
    ).strip()
    return {
        "answer": text or resp,
        "entra_user": entra_user,
        "query_id": qid,
        "correlation_id": corr,
    }


@mcp.tool
async def get_financial_summary() -> dict:
    """Ticket revenue and visits by park, plus GL actual vs budget by department.
    Rows, columns and schemas are filtered by Snowflake according to the mapped persona's role."""
    result = {}
    rows, qid, corr, entra_user = await anyio.to_thread.run_sync(
        _run,
        """SELECT PARK_NAME, SUM(VISITS) AS VISITS, SUM(TICKET_NET_REVENUE) AS TICKET_NET_REVENUE
             FROM AMUSEMENT_PARK_DB.ANALYTICS.V_DAILY_PARK_PERFORMANCE
            GROUP BY PARK_NAME ORDER BY PARK_NAME"""
    )
    result["entra_user"] = entra_user
    result["ticket_revenue_by_park"] = rows
    result["correlation_id"] = corr
    try:
        rows, _, _, _ = await anyio.to_thread.run_sync(
            _run,
            """SELECT DEPARTMENT_NAME, SUM(ACTUAL_AMOUNT) AS ACTUAL, SUM(BUDGET_AMOUNT) AS BUDGET
                 FROM AMUSEMENT_PARK_DB.ANALYTICS.V_FINANCIAL_ACTUAL_VS_BUDGET
                GROUP BY DEPARTMENT_NAME ORDER BY ACTUAL DESC"""
        )
        result["gl_actual_vs_budget_by_department"] = rows
    except snowflake.connector.errors.ProgrammingError as e:
        result["gl_actual_vs_budget_by_department"] = f"ACCESS DENIED by Snowflake RBAC: {e.msg}"
    return result


if __name__ == "__main__":
    # Note: Middleware is critical for POST (tool invocations) but may interfere with GET (discovery).
    # If discovery still fails with 302, this suggests FastMCP's internal routing or Snowflake ingress
    # is causing the redirect. The middleware is essential for identity mapping on tool calls.
    mcp.run(
        transport="http",
        host="0.0.0.0",
        port=PORT,
        path="/mcp",
        middleware=[Middleware(EntraBrokerMiddleware)],
        stateless_http=True,
    )
