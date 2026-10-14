# Complete Deployment Guide for Amusement Park MCP

This guide walks your teammate through deploying the entire MCP server to their own Snowflake environment.

## Prerequisites

- **Snowflake Account** (with ACCOUNTADMIN role)
- **Docker** installed locally
- **Git** installed
- **Snowflake CLI** (`snow`) installed
- **Python 3.11+** (for local testing)

## Step 1: Clone the Repository

```bash
git clone https://github.com/dkrunal90/park-mcp.git
cd park-mcp
```

## Step 2: Setup Environment Variables

```bash
# Copy the example environment file
cp .env.example .env

# Edit with your Snowflake details
nano .env
```

**Required values to update in `.env`:**
```env
SNOWFLAKE_ACCOUNT=your-account-id           # e.g., xy12345
SNOWFLAKE_HOST=your-account-id.snowflakecomputing.com
SNOWFLAKE_WAREHOUSE=your-warehouse          # e.g., COMPUTE_WH
SNOWFLAKE_DATABASE=your-database            # e.g., AMUSEMENT_PARK_DB
SNOWFLAKE_SCHEMA=your-schema                # e.g., ANALYTICS
MCP_API_KEY=your-secure-api-key             # Generate a strong key
AGENT_FQN=your_db.your_schema.your_agent    # Your Cortex Agent path
```

## Step 3: Configure Snowflake CLI

```bash
# List existing connections
snow connection list

# Create a new connection (if needed)
snow connection add \
  --username YOUR_USERNAME \
  --account your-account-id \
  --database your-database \
  --schema your-schema \
  --warehouse your-warehouse \
  --role ACCOUNTADMIN \
  --connection-name poc

# Test the connection
snow connection test -c poc
```

## Step 4: Deploy Database Objects to Snowflake

Run the SQL setup scripts in order:

```bash
# 1. Setup identity roles and policies
snow sql -c poc -f 06_mcp_poc_identity.sql

# 2. Setup SPCS infrastructure
snow sql -c poc -f 07_mcp_poc_spcs.sql

# 3. Setup Entra ID mapping (IMPORTANT: Update with your users!)
# Edit 08_mcp_entra_mapping.sql to add your team's Entra IDs
# Then run:
# snow sql -c poc -f 08_mcp_entra_mapping.sql
```

⚠️ **Important:** Before running 08_mcp_entra_mapping.sql, edit it to replace:
- `ceo@amusementpark.com` → your CEO's email
- `analyst@amusementpark.com` → your analyst's email
- `MCP_POC_CEO`, `MCP_POC_ANALYST` → your user names

## Step 5: Build and Push Docker Image

### 5a. Login to Snowflake Registry

```bash
snow spcs image-registry login -c poc
```

### 5b. Build the Docker Image

```bash
# Set your registry URL (update ACCOUNT_ID)
export REPO=ACCOUNT_ID.registry.snowflakecomputing.com/database_name/schema_name/repo_name

# Build for Linux (required for SPCS)
docker build --platform linux/amd64 -t $REPO/park-mcp:latest mcp_poc/

# Verify build
docker images | grep park-mcp
```

### 5c. Push to Snowflake Registry

```bash
docker push $REPO/park-mcp:latest

# Note the digest (hash) shown in output
# Example: sha256:abc123def456...
```

## Step 6: Deploy to Snowflake SPCS

### 6a. Create Deployment SQL

Edit `deploy_service.sql` (create this file):

```sql
USE ROLE MCP_SERVICE_OWNER;
ALTER SERVICE AMUSEMENT_PARK_DB.ANALYTICS.MCP_POC_SERVICE FROM SPECIFICATION $$
spec:
  containers:
  - name: mcp
    image: /your_database/your_schema/your_repo/park-mcp:latest
    env:
      SERVER_PORT: 8080
      SNOWFLAKE_WAREHOUSE: COMPUTE_WH
      RELOAD_TRIGGER: "v1"
    secrets:
    - snowflakeSecret: AMUSEMENT_PARK_DB.ANALYTICS.MCP_API_KEY
      secretKeyRef: secret_string
      envVarName: MCP_API_KEY
    readinessProbe:
      port: 8080
      path: /healthz
  endpoints:
  - name: mcp
    port: 8080
    public: true
capabilities:
  securityContext:
    executeAsCaller: true
serviceRoles:
- name: mcp_user
  endpoints:
  - mcp
$$;
```

### 6b. Deploy the Service

```bash
snow sql -c poc -f deploy_service.sql

# Wait ~30 seconds for container to start
sleep 30

# Check service status
snow sql -c poc -q "SHOW SERVICE CONTAINERS IN SERVICE database_name.schema_name.MCP_POC_SERVICE;"

# Get the public endpoint
snow sql -c poc -q "SHOW ENDPOINTS IN SERVICE database_name.schema_name.MCP_POC_SERVICE;"
```

Note the `ingress_url` from the output.

## Step 7: Test the Deployment

### 7a. Local Testing (Optional)

```bash
# Setup Python environment
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Install dependencies
pip install -r mcp_poc/requirements.txt httpx requests

# Run tests
cd mcp_poc
python test_client.py
# When prompted, enter your Snowflake PATs
```

### 7b. Test Live Endpoint

```bash
# Get your endpoint URL from Step 6b
ENDPOINT="https://your-account-xxxxx.snowflakecomputing.app/mcp"

# Test discovery (should return 200 with tool list)
curl -s $ENDPOINT | jq .

# Test a tool call
curl -X POST $ENDPOINT \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_PAT" \
  -H "X-API-Key: YOUR_MCP_API_KEY" \
  -H "X-Entra-User: your-email@company.com" \
  -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"whoami"},"id":1}'
```

## Step 8: Integrate with Azure AI Foundry (Optional)

1. Go to [Azure AI Foundry](https://ai.azure.com)
2. Create/Open your project
3. Navigate to **Agents** → **Tools**
4. Click **Add Tool** → **Model Context Protocol**
5. Configure:
   - **Name:** park-mcp
   - **Endpoint:** Your `ingress_url` from Step 6b
   - **Authentication Type:** Key-based
   - **Authorization:** `Snowflake Token=YOUR_PAT`
   - **X-API-Key:** `YOUR_MCP_API_KEY`
   - **X-Entra-User:** `your-email@company.com`
6. Click **Add**
7. Test in agent chat

## Troubleshooting

### Service fails to start
```bash
# Check logs
snow sql -c poc -q "SELECT SYSTEM\$GET_SERVICE_LOGS('database.schema.MCP_POC_SERVICE', 0, 'mcp', 100);"
```

### 302 Redirect on Tool Discovery
- Ensure `Authorization` header is in format: `Snowflake Token=YOUR_PAT`
- Not: `Bearer YOUR_PAT`

### API Key Validation Fails
- Verify `MCP_API_KEY` in `.env` matches what you're sending in `X-API-Key` header

### Identity Mapping Not Working
- Check `ENTRA_USER_MAP` table exists and has your users:
  ```sql
  SELECT * FROM AMUSEMENT_PARK_DB.GOVERNANCE.ENTRA_USER_MAP;
  ```

## Updating the Deployment

After making code changes:

```bash
# Rebuild image
docker build --platform linux/amd64 -t $REPO/park-mcp:latest mcp_poc/

# Push to registry
docker push $REPO/park-mcp:latest

# Update RELOAD_TRIGGER in deploy_service.sql (increment v1→v2, etc)
# Then redeploy:
snow sql -c poc -f deploy_service.sql

# Wait for restart and verify
sleep 30
snow sql -c poc -q "SHOW SERVICE CONTAINERS IN SERVICE ..."
```

## File Structure

```
park-mcp/
├── .env                          (Local - not in git)
├── .env.example                  (Template - in git)
├── .env.setup.md                 (Setup instructions)
├── .gitignore                    (Excludes secrets)
├── README.md                     (Overview)
├── DEPLOYMENT.md                 (This file)
├── Makefile                      (Build automation)
├── mcp_poc/
│   ├── server.py                 (MCP server code)
│   ├── test_client.py            (End-to-end tests)
│   ├── Dockerfile                (Container image)
│   ├── requirements.txt           (Python dependencies)
│   └── RUNBOOK.md                (Operations guide)
├── 06_mcp_poc_identity.sql       (Roles & policies)
├── 07_mcp_poc_spcs.sql           (SPCS infrastructure)
└── foundry_connect.py            (Foundry integration)
```

## What Gets Deployed

✅ **MCP Server:** FastMCP with 3 tools
- `whoami` - Identity verification
- `ask_park_insights` - Natural language query via Cortex
- `get_financial_summary` - Data with role-based filtering

✅ **Snowflake Objects:**
- Roles: `PARK_CEO`, `PARK_ANALYST`, `MCP_SERVICE_OWNER`
- Users: `MCP_POC_CEO`, `MCP_POC_ANALYST`
- Policies: Row Access + Column Masking
- Views: Governed data views
- Agent: Cortex Data Agent

✅ **SPCS Service:**
- Public HTTPS endpoint
- OAuth-secured ingress
- Auto health checks

## Security Checklist

- [ ] `.env` file is local and not committed
- [ ] `MCP_API_KEY` is rotated from examples
- [ ] Snowflake PATs are generated per user
- [ ] RBAC policies are tested
- [ ] Entra ID mapping reflects your team
- [ ] Service endpoint is HTTPS only
- [ ] Container image is scanned for vulnerabilities

## Next Steps

1. Customize Entra ID mappings for your team
2. Add your own data views to AMUSEMENT_PARK_DB
3. Test with your business questions
4. Deploy to Azure AI Foundry agents
5. Monitor logs and performance

For more details, see [README.md](README.md) and [RUNBOOK.md](mcp_poc/RUNBOOK.md)
