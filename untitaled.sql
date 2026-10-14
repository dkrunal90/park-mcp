USE ROLE MCP_SERVICE_OWNER;
ALTER SERVICE AMUSEMENT_PARK_DB.ANALYTICS.MCP_POC_SERVICE FROM SPECIFICATION $$
spec:
  containers:
  - name: mcp
    image: /amusement_park_db/analytics/mcp_repo/park-mcp:latest
    env:
      SERVER_PORT: 8080
      SNOWFLAKE_WAREHOUSE: COMPUTE_WH
      RELOAD_TRIGGER: "v5"
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