.PHONY: setup test-sf local build push deploy status logs endpoints test suspend resume destroy clean help

REPO := tqmttqp-hw26207.registry.snowflakecomputing.com/amusement_park_db/analytics/mcp_repo
IMAGE := $(REPO)/park-mcp:latest
VENV := .venv
PYTHON := python3
PIP := $(VENV)/bin/pip
PYTHON_RUN := $(VENV)/bin/python

help:
	@echo "Amusement Park MCP Server — Build & Deploy"
	@echo ""
	@echo "Setup & Configuration:"
	@echo "  make setup              Create .env, Python venv, install deps"
	@echo "  make test-sf            Test Snowflake CLI connection"
	@echo ""
	@echo "Local Development:"
	@echo "  make local              Run FastAPI locally (port 8000)"
	@echo ""
	@echo "Build & Deploy:"
	@echo "  make build              Build Docker image (linux/amd64)"
	@echo "  make push               Push image to Snowflake registry"
	@echo "  make deploy             Deploy/update service in SPCS"
	@echo ""
	@echo "Operations:"
	@echo "  make status             Show service status"
	@echo "  make logs               Show recent service logs"
	@echo "  make endpoints          Show public HTTPS endpoint"
	@echo "  make test               Run end-to-end tests (CEO + Analyst)"
	@echo "  make foundry-connect    Connect to Azure AI Foundry via SDK"
	@echo ""
	@echo "Maintenance:"
	@echo "  make suspend            Suspend compute pool (stop billing)"
	@echo "  make resume             Resume compute pool"
	@echo "  make destroy            Drop service (keep data)"
	@echo "  make clean              Remove .venv and build artifacts"
	@echo ""

setup:
	@echo "=== Setting up Python environment ==="
	$(PYTHON) -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r mcp_poc/requirements.txt httpx requests
	@echo ""
	@echo "✅ Environment ready!"
	@echo "   Run: . $(VENV)/bin/activate"
	@echo "   Then: make test-sf"

test-sf:
	@echo "=== Testing Snowflake CLI connection ==="
	snow connection test -c poc
	@echo "✅ Connection OK"

local:
	@echo "=== Running FastAPI locally (port 8000) ==="
	. $(VENV)/bin/activate && cd mcp_poc && python -m uvicorn server:app --host 0.0.0.0 --port 8000 --reload

build:
	@echo "=== Building Docker image ==="
	docker build --platform linux/amd64 -t $(IMAGE) mcp_poc/
	@echo "✅ Image built: $(IMAGE)"

push: build
	@echo "=== Authenticating with Snowflake registry ==="
	snow spcs image-registry login -c poc
	@echo ""
	@echo "=== Pushing image to registry ==="
	docker push $(IMAGE)
	@echo "✅ Image pushed"

deploy:
	@echo "=== Deploying to SPCS ==="
	@echo ""
	@echo "Run this in Snowflake (VS Code Snowflake extension or worksheet):"
	@echo ""
	@echo "USE ROLE MCP_SERVICE_OWNER;"
	@echo "ALTER SERVICE AMUSEMENT_PARK_DB.ANALYTICS.MCP_POC_SERVICE FROM SPECIFICATION \$$\$$"
	@echo "spec:"
	@echo "  containers:"
	@echo "  - name: mcp"
	@echo "    image: /amusement_park_db/analytics/mcp_repo/park-mcp:latest"
	@echo "    env:"
	@echo "      SERVER_PORT: 8080"
	@echo "      SNOWFLAKE_WAREHOUSE: COMPUTE_WH"
	@echo "      RELOAD_TRIGGER: \"v5\""
	@echo "    secrets:"
	@echo "    - snowflakeSecret: AMUSEMENT_PARK_DB.ANALYTICS.MCP_API_KEY"
	@echo "      secretKeyRef: secret_string"
	@echo "      envVarName: MCP_API_KEY"
	@echo "    readinessProbe:"
	@echo "      port: 8080"
	@echo "      path: /healthz"
	@echo "  endpoints:"
	@echo "  - name: mcp"
	@echo "    port: 8080"
	@echo "    public: true"
	@echo "capabilities:"
	@echo "  securityContext:"
	@echo "    executeAsCaller: true"
	@echo "serviceRoles:"
	@echo "- name: mcp_user"
	@echo "  endpoints:"
	@echo "  - mcp"
	@echo "\$$\$$;"
	@echo ""
	@echo "Then wait ~30 seconds and run: make status"

status:
	@echo "=== Checking service status ==="
	@echo "Run in Snowflake:"
	@echo ""
	@echo "SHOW SERVICE CONTAINERS IN SERVICE AMUSEMENT_PARK_DB.ANALYTICS.MCP_POC_SERVICE;"
	@echo ""

logs:
	@echo "=== Fetching service logs ==="
	@echo "Run in Snowflake:"
	@echo ""
	@echo "SELECT SYSTEM\$$GET_SERVICE_LOGS('AMUSEMENT_PARK_DB.ANALYTICS.MCP_POC_SERVICE', 0, 'mcp', 50);"
	@echo ""

endpoints:
	@echo "=== Getting service endpoint ==="
	@echo "Run in Snowflake:"
	@echo ""
	@echo "SHOW ENDPOINTS IN SERVICE AMUSEMENT_PARK_DB.ANALYTICS.MCP_POC_SERVICE;"
	@echo ""
	@echo "Look for: ingress_url"

test:
	@echo "=== Running end-to-end tests ==="
	. $(VENV)/bin/activate && cd mcp_poc && \
	read -s -p "CEO PAT: " CEO_PAT; echo; \
	read -s -p "Analyst PAT: " ANALYST_PAT; echo; \
	export CEO_PAT="$$CEO_PAT" ANALYST_PAT="$$ANALYST_PAT"; \
	export MCP_URL="https://abz2pr-tqmttqp-hw26207.snowflakecomputing.app/mcp"; \
	export MCP_API_KEY=123456; \
	$(PYTHON_RUN) test_client.py

foundry-connect:
	@echo "=== Testing Amusement Park MCP with Azure AI Foundry ==="
	@echo ""
	@echo "Step 1: Install Azure AI Projects SDK"
	@echo "  pip install 'azure-ai-projects>=2.1.0'"
	@echo ""
	@echo "Step 2: Set REQUIRED environment variables:"
	@echo "  export CEO_PAT='<snowflake-ceo-pat>'"
	@echo "  export ANALYST_PAT='<snowflake-analyst-pat>'"
	@echo "  export AZURE_PROJECT_ENDPOINT='https://test-eval-1.services.ai.azure.com/api/projects/proj-default'"
	@echo "  export AGENT_NAME='agent-POC'"
	@echo ""
	@echo "Step 3: Find your values:"
	@echo "  1. Project Endpoint:"
	@echo "     - Go to Azure AI Foundry portal"
	@echo "     - Open your project"
	@echo "     - Copy full endpoint URL from Settings → Project details"
	@echo "  2. Agent Name:"
	@echo "     - Go to Agents tab"
	@echo "     - Copy agent name (e.g., 'agent-POC')"
	@echo ""
	@echo "Step 4: Run this script:"
	@echo ""
	. $(VENV)/bin/activate && $(PYTHON_RUN) foundry_connect.py

suspend:
	@echo "=== Suspending compute pool (stops billing) ==="
	@echo "Run in Snowflake:"
	@echo ""
	@echo "USE ROLE ACCOUNTADMIN;"
	@echo "ALTER COMPUTE POOL MCP_POC_POOL STOP ALL;"
	@echo "ALTER COMPUTE POOL MCP_POC_POOL SUSPEND;"
	@echo ""

resume:
	@echo "=== Resuming compute pool ==="
	@echo "Run in Snowflake:"
	@echo ""
	@echo "USE ROLE ACCOUNTADMIN;"
	@echo "ALTER COMPUTE POOL MCP_POC_POOL RESUME;"
	@echo ""
	@echo "Then: make deploy"

destroy:
	@echo "=== Destroying service (keeps data) ==="
	@echo "Run in Snowflake:"
	@echo ""
	@echo "USE ROLE ACCOUNTADMIN;"
	@echo "DROP SERVICE AMUSEMENT_PARK_DB.ANALYTICS.MCP_POC_SERVICE;"
	@echo ""

clean:
	@echo "=== Cleaning up ==="
	rm -rf $(VENV)
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	@echo "✅ Cleaned"

all: setup build push deploy test
	@echo "✅ All done!"
