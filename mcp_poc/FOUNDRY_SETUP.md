# Connect the Azure AI Foundry agent to the Snowflake MCP server

Foundry connects directly to the **Snowflake-managed MCP server** `AMUSEMENT_PARK_DB.ANALYTICS.AMUSEMENT_PARK_MCP_SERVER`. There is no container and no Docker. Each persona authenticates with its **own Snowflake PAT**. Snowflake runs the agent as that user, so the CEO connection and the Analyst connection return different data.

## 1. Values you need

| Item | Value |
|---|---|
| MCP server URL | `https://tqmttqp-hw26207.snowflakecomputing.com/api/v2/databases/AMUSEMENT_PARK_DB/schemas/ANALYTICS/mcp-servers/AMUSEMENT_PARK_MCP_SERVER` |
| CEO PAT | `FOUNDRY_CEO` on user `MCP_POC_CEO` (role `PARK_CEO`, 30 days) |
| Analyst PAT | `FOUNDRY_ANALYST` on user `MCP_POC_ANALYST` (role `PARK_ANALYST`, 30 days) |

Both PATs were created on 2026-10-12. Snowflake shows a PAT secret only once. To issue a new one (this invalidates nothing else):
```sql
ALTER USER MCP_POC_CEO     REMOVE PROGRAMMATIC ACCESS TOKEN FOUNDRY_CEO;
ALTER USER MCP_POC_CEO     ADD PROGRAMMATIC ACCESS TOKEN FOUNDRY_CEO     ROLE_RESTRICTION='PARK_CEO'     DAYS_TO_EXPIRY=30;
ALTER USER MCP_POC_ANALYST REMOVE PROGRAMMATIC ACCESS TOKEN FOUNDRY_ANALYST;
ALTER USER MCP_POC_ANALYST ADD PROGRAMMATIC ACCESS TOKEN FOUNDRY_ANALYST ROLE_RESTRICTION='PARK_ANALYST' DAYS_TO_EXPIRY=30;
```

## 2. Request headers

| Header | Value |
|---|---|
| `Authorization` | `Bearer <PAT>` |
| `X-Snowflake-Authorization-Token-Type` | `PROGRAMMATIC_ACCESS_TOKEN` |

## 3. Add the MCP tool in Foundry

Create **two MCP tool connections** (or two agents), one per persona, each set up once. Names and labels in the Foundry portal and SDK change often, so check them against the current Foundry docs.

**Portal:** Agent → *Tools* → *Add* → *Model Context Protocol (MCP)*.
- Server label: `park_mcp_ceo` (or `park_mcp_analyst`). Use hyphens or underscores in labels, but **never underscores in the hostname**.
- Server URL: the URL in section 1
- Custom headers: the two headers in section 2
- Approval: *Never require approval*, so the demo runs without prompts

**Python SDK (azure-ai-agents), sketch:**
```python
from azure.ai.agents.models import McpTool

mcp = McpTool(server_label="park_mcp_ceo",
              server_url=MCP_URL,
              allowed_tools=["amusement_park_insights"])
mcp.update_headers("Authorization", f"Bearer {CEO_PAT}")
mcp.update_headers("X-Snowflake-Authorization-Token-Type", "PROGRAMMATIC_ACCESS_TOKEN")
mcp.set_approval_mode("never")
```

## 4. Suggested agent instructions
> You answer amusement park business questions. Always call `amusement_park_insights` for questions about rides, sales, revenue, expenses or departments. Never guess numbers. If data is missing, masked or access is denied, say so plainly.

## 5. Troubleshooting

| Symptom | Cause / fix |
|---|---|
| 401 | PAT missing, expired, or `Bearer` prefix missing. |
| PAT rejected: network policy | The user lost the `MCP_POC_PAT_POLICY` authentication policy, or a network policy blocks Foundry's IPs. |
| "not authorized" on the MCP server or tool | The persona role lacks USAGE on `AMUSEMENT_PARK_MCP_SERVER` or on `AMUSEMENT_PARK_INSIGHTS_AGENT`. |
| Connection errors on the hostname | Use `tqmttqp-hw26207`, with a hyphen, not an underscore. |
| Analyst answer lacks finance data | Expected. The Analyst role has no FINANCE access. |
