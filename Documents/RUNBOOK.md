# Runbook: per-user MCP access from Azure AI Foundry to Snowflake

**Claim being demonstrated:** when the Foundry agent calls the MCP server, the CEO and an entry-level analyst can ask the same question and each receives only the data their Snowflake role permits. Every query is attributed to the real user, not a shared service account.

## Architecture
```
Foundry agent ──HTTPS + Bearer PAT──▶ Snowflake-managed MCP server
                                       AMUSEMENT_PARK_DB.ANALYTICS.AMUSEMENT_PARK_MCP_SERVER
                                       │ runs AS THE PAT OWNER (MCP_POC_CEO / MCP_POC_ANALYST)
                                       ▼
            Cortex Agent AMUSEMENT_PARK_INSIGHTS_AGENT ──▶ RBAC + Row Access Policy + Masking Policy
```
No container, no Docker, no service account. The PAT identifies the user and Snowflake applies that user's role.

## What is configured

| Control | Object | Effect |
|---|---|---|
| Personas | `MCP_POC_CEO` → `PARK_CEO`; `MCP_POC_ANALYST` → `PARK_ANALYST` | Separate identities, separate PATs |
| MCP access | USAGE on `AMUSEMENT_PARK_MCP_SERVER` and `AMUSEMENT_PARK_INSIGHTS_AGENT` for both roles | Only these roles (and admins) can call it |
| Schema RBAC | Analyst has no `FINANCE` schema and no `FINANCIALS_SV` | GL and budget are invisible to the analyst |
| Row access | `GOVERNANCE.RAP_PARK_SCOPE` on 6 OPS fact tables | Analyst sees park 1 only (Mountain Peaks) |
| Masking | `GOVERNANCE.MP_MASK_TEXT` / `MP_MASK_NUMBER` | Guest/employee names → `***MASKED***`; hourly rate and labour cost → NULL |
| PATs | `FOUNDRY_CEO`, `FOUNDRY_ANALYST`, role-restricted, 30 days | Created 2026-10-12 |
| PAT policy | `GOVERNANCE.MCP_POC_PAT_POLICY` | PoC only: PAT without a network policy, 30-day max |

Verified in SQL: `PARK_CEO` sees 3 parks ($47.5M outlet net revenue), a max rate of 52.81 and real names. `PARK_ANALYST` sees 1 park ($15.9M), a NULL rate and `***MASKED***`.

## Deploy steps

1. `06_mcp_poc_identity.sql`: **done** (roles, users, policies, PAT policy).
2. MCP server and agent grants to both roles: **done**.
3. PATs: **done**. Re-issue them with the SQL in `FOUNDRY_SETUP.md` section 1 if lost.
4. Run `python test_client.py` from your machine. The CoCo sandbox blocks outbound HTTPS, so it could not run there.
5. Configure Foundry per `FOUNDRY_SETUP.md`.

`server.py`, `Dockerfile` and `07_mcp_poc_spcs.sql` (the SPCS container option) are no longer needed. They are kept only in case a custom server is wanted later.

## Demo script (about 10 minutes)

1. **No credential:** run `test_client.py`. Calls with no PAT or a fake PAT are rejected by Snowflake.
2. **Who is asking:** show the two Foundry connections, each with its own PAT. No shared credential exists.
3. **Same question in Foundry, both personas:** *"What was ticket revenue by park last quarter, and what's our highest employee hourly rate?"*
   - CEO: all 3 parks, actual rate.
   - Analyst: Mountain Peaks only, rate unavailable or masked.
4. **"Show GL actual vs budget by department":**
   - CEO: full table.
   - Analyst: no finance data available to this role.
5. **Audit evidence:** run the query below. Each query is listed under the real persona.

## Evidence queries
```sql
-- Who ran what through the MCP server (QUERY_HISTORY is near real time)
SELECT start_time, user_name, role_name, query_tag, LEFT(query_text, 120) AS query_text
FROM TABLE(INFORMATION_SCHEMA.QUERY_HISTORY(RESULT_LIMIT => 200))
WHERE user_name IN ('MCP_POC_CEO','MCP_POC_ANALYST')
ORDER BY start_time DESC;

-- Which objects/columns each persona touched (ACCOUNT_USAGE lags up to ~3h)
SELECT query_start_time, user_name, f.value:"objectName"::string AS object_name
FROM SNOWFLAKE.ACCOUNT_USAGE.ACCESS_HISTORY, LATERAL FLATTEN(base_objects_accessed) f
WHERE user_name IN ('MCP_POC_CEO','MCP_POC_ANALYST')
ORDER BY query_start_time DESC;

-- Policies in force
SELECT * FROM TABLE(AMUSEMENT_PARK_DB.INFORMATION_SCHEMA.POLICY_REFERENCES(
  REF_ENTITY_NAME => 'AMUSEMENT_PARK_DB.OPS.FACT_OUTLET_SALE', REF_ENTITY_DOMAIN => 'table'));
```

## PoC shortcuts to name up front (for security)

| PoC | Production |
|---|---|
| One PAT per persona, stored in Foundry | **Entra ID + Snowflake External OAuth.** Foundry passes the signed-in user's token (on-behalf-of flow); Snowflake maps `upn` to the user. No stored secrets. |
| `MCP_POC_PAT_POLICY` skips the network policy requirement | Network policy that allows only Foundry/Azure egress IPs or Private Link |
| Hard-coded park filter in the row access policy | Mapping table (role/group → park/department) driven by Entra groups |

Everything after authentication (caller's rights, RBAC, row access, masking, audit) stays exactly the same in production. That is the part this PoC proves.

## Cleanup
```sql
DROP COMPUTE POOL IF EXISTS MCP_POC_POOL;   -- created for the unused container option
ALTER USER MCP_POC_CEO REMOVE PROGRAMMATIC ACCESS TOKEN FOUNDRY_CEO;
ALTER USER MCP_POC_ANALYST REMOVE PROGRAMMATIC ACCESS TOKEN FOUNDRY_ANALYST;
```
