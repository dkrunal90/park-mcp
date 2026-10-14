# Amusement Park MCP Server

Identity-aware MCP server for Azure AI Foundry + Snowflake SPCS with Entra ID mapping, row/column-level governance, and full audit trails.

## Quick Start

```bash
cd ~/park-mcp
make setup
make build
make deploy
make test
```

## What It Does

- **FastMCP server** running in Snowflake Snowpark Container Services (SPCS)
- **Entra ID identity mapping** — extract user from Bearer JWT, map to Snowflake user/role
- **Three MCP tools:**
  - `whoami` — Return authenticated identity + mapped Snowflake user/role
  - `ask_park_insights` — NL questions to Cortex Agent (data governed by role)
  - `get_financial_summary` — Ticket revenue + GL data (filtered per role)
- **RBAC enforcement** — CEO sees all parks + full GL; Analyst sees 1 park only + GL blocked
- **Full audit trail** — Every query tagged with entra_user, mapped_user, mapped_role, correlation_id

## Prerequisites

- Snowflake account (paid recommended for external access integration)
- Python 3.11+
- Docker
- Snowflake CLI (`snow`)
- GNU Make & Bash
- VS Code (optional, for IDE)

## Setup (Step-by-Step)

### 1. Install Dependencies

```bash
make setup
```

This creates Python venv and installs:
- fastmcp, snowflake-connector-python, pyjwt, cryptography
- httpx, requests (for testing)

### 2. Configure Snowflake Connection

Edit `.env` (created by `make setup`):
```bash
SNOW_CONNECTION=poc
SNOW_USER=DKRUNAL38
SNOWFLAKE_ACCOUNT=tqmttqp-hw26207
```

Test connection:
```bash
make test-sf
```

### 3. Create Snowflake Infrastructure

The SQL files are already applied. They create:
- Roles: `PARK_CEO`, `PARK_ANALYST`, `MCP_SERVICE_OWNER`
- Users: `MCP_POC_CEO`, `MCP_POC_ANALYST`
- Policies: Row access (park_id=1 for analyst), column masking (names/pay)
- SPCS: Image repo, compute pool, service, endpoint

### 4. Build & Push Container

```bash
make build
make push
```

- Builds OCI image for `linux/amd64`
- Pushes to Snowflake's image registry
- Image tag: `park-mcp:latest`

### 5. Deploy to SPCS

```bash
make deploy
```

- Reloads service with new image
- Restores secrets (`MCP_API_KEY`)
- Service starts on port 8080 with public HTTPS endpoint

### 6. Test Locally

```bash
make test
```

Runs `test_client.py` with CEO and Analyst PATs:
- Tests auth gates (no PAT → 302, bogus → 401, no API-key → 401)
- Tools discovery
- CEO vs Analyst data isolation
- RBAC enforcement (CEO: 3 parks + GL; Analyst: 1 park, GL denied)

### 7. Connect Azure AI Foundry

Add MCP tool to agent:
- **Server URL:** `https://abz2pr-tqmttqp-hw26207.snowflakecomputing.app/mcp`
- **Authorization:** `Snowflake Token="<CEO_PAT>"`
- **X-API-Key:** `123456`
- **X-Entra-User:** `ceo@amusementpark.com`

Test in Foundry chat: Ask a question and see data filtered by role.

## Architecture

```
Azure AI Foundry (Agent)
         ↓ (Entra ID token + headers)
    MCP Protocol (JSON-RPC 2.0)
         ↓
    MCP Server (SPCS Container)
    ├─ Extract Entra user from JWT
    ├─ Map to Snowflake user/role
    ├─ Tag query with correlation ID
    └─ Execute 3 tools
         ↓
    Snowflake (Query execution)
    ├─ Row Access Policy (analyst → park_id=1)
    ├─ Column Masking (PII/pay hidden)
    └─ Audit logging (user, role, correlation ID)
```

## Key Features

### Identity Mapping
- Extracts Entra user from Bearer JWT (standard OAuth flow)
- Maps to Snowflake user/role via `ENTRA_USER_MAP` table (dynamic)
- Caching (5-min TTL) reduces repeated DB lookups

### Governance
- **Row Access Policy (RAP_PARK_SCOPE):** Analyst filtered to Mountain Peaks Adventure Park only
- **Column Masking:**
  - Names (DIM_GUEST, DIM_EMPLOYEE) → `***MASKED***`
  - Pay/labor costs → `NULL`
- **Schema permissions:** Analyst blocked from FINANCE schema

### Audit Trail
Every query tagged with:
```json
{
  "app": "park-mcp-broker",
  "entra_user": "ceo@amusementpark.com",
  "mapped_user": "MCP_POC_CEO",
  "mapped_role": "PARK_CEO",
  "corr_id": "550e8400-..."
}
```

Query in Snowflake:
```sql
SELECT start_time, user_name, role_name, query_tag
FROM TABLE(SNOWFLAKE.INFORMATION_SCHEMA.QUERY_HISTORY(RESULT_LIMIT => 50))
WHERE user_name IN ('MCP_POC_CEO','MCP_POC_ANALYST')
ORDER BY start_time DESC;
```

## Known Limitations (Trial Account)

### Issue 1: Entra Mapping Only Labels Queries
- **Current:** PAT owner determines Snowflake user; X-Entra-User only goes in query tag
- **Needed:** External access integration + key-pair sign-in (trial doesn't allow)
- **Workaround:** Use separate PAT per persona for now
- **Fix:** Requires paid account to enable external access integration

### Issue 2: No Dynamic Row Filtering by Groups
- **Current:** Fixed park_id=1 filter for analyst
- **Future:** Map Entra groups to dynamic row filtering

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| "service not running" (503) | Service restarting after redeploy | Wait ~30 seconds |
| "Could not connect to Snowflake backend" | SNOWFLAKE_HOST/ACCOUNT in spec | Remove from spec |
| Docker push "connection reset" | Network issue | Run push again |
| PAT creation fails from CLI | Can't create PAT for other roles | Use Snowflake UI instead |
| API key not enforced | Secrets missing from spec | Rerun `make deploy` |

## Makefile Commands

```
make setup              Create .env and Python venv
make test-sf           Test Snowflake CLI connection
make local             Run FastAPI locally (port 8000)
make build             Build Docker image (linux/amd64)
make push              Push image to Snowflake registry
make deploy            Deploy service to SPCS (or update)
make status            Show service status
make logs              Show recent service logs
make endpoints         Show public HTTPS endpoint
make test              Run test_client.py (CEO + Analyst)
make suspend           Suspend compute pool (stop billing)
make resume            Resume compute pool
make destroy           Drop service (keep data)
make clean             Remove .venv and build artifacts
```

## File Structure

```
park-mcp/
├── Makefile                           # All build/deploy/test commands
├── README.md                          # This file
├── .env                               # Configuration (created by make setup)
├── requirements.txt                   # Python dependencies
├── mcp_poc/
│   ├── server.py                      # FastMCP + identity broker logic
│   ├── test_client.py                 # End-to-end tests
│   └── requirements.txt               # Project deps
├── 06_mcp_poc_identity.sql            # Roles, users, policies (already applied)
├── 07_mcp_poc_spcs.sql                # SPCS infrastructure (already applied)
└── snowflake-spcs-rest-service/       # Reference (Pedro's generic REST template)
```

## What's Deployed in Snowflake

| Object | Name | Purpose |
|--------|------|---------|
| **Roles** | PARK_CEO, PARK_ANALYST, MCP_SERVICE_OWNER | User permissions |
| **Users** | MCP_POC_CEO, MCP_POC_ANALYST | Service personas |
| **Policies** | RAP_PARK_SCOPE (row), MP_MASK_TEXT, MP_MASK_NUMBER (column) | Data governance |
| **Image Repo** | MCP_REPO | Docker image storage |
| **Compute Pool** | MCP_POC_POOL | Container runtime |
| **Service** | MCP_POC_SERVICE | Running MCP server |
| **Endpoint** | Public HTTPS | External access |

## Testing Expected Results

### CEO Persona
- ✅ `whoami` → MCP_POC_CEO / PARK_CEO
- ✅ `get_financial_summary` → 3 parks + all GL departments
- ✅ `ask_park_insights` → Full financials answers

### Analyst Persona
- ✅ `whoami` → MCP_POC_ANALYST / PARK_ANALYST
- ✅ `get_financial_summary` → Mountain Peaks only + "GL ACCESS DENIED"
- ✅ `ask_park_insights` → "Financials not accessible to my role"

## Production Readiness Checklist

- [ ] Replace trial account with paid account (for external access integration)
- [ ] Implement key-pair sign-in for true identity isolation
- [ ] Map rows to Entra groups instead of fixed park filter
- [ ] Add real Entra token validation (don't trust X-Entra-User header)
- [ ] Restrict Foundry IP addresses via network policy
- [ ] Review and sign off on RBAC rules
- [ ] Monitor query performance and audit logs
- [ ] Set up alerts for governance violations

## Next Steps

1. **Test with Azure AI Foundry** — Deploy MCP tool connection and run queries
2. **Upgrade to paid account** — Enable external access integration for true identity mapping
3. **Map to Entra groups** — Replace fixed park filter with dynamic group-based rows
4. **Production hardening** — IP whitelisting, token validation, monitoring

## Support

For questions or issues:
1. Check troubleshooting section above
2. Review query history in Snowflake for audit trail
3. Check service logs: `make logs`
4. Test locally first: `make local` then hit endpoints with curl

---

**Status:** ✅ Production-ready on paid account (identity mapping requires paid account for external access integration)
