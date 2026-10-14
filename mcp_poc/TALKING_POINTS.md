# Azure AI Foundry & Entra ID Identity Broker Architecture

## Overview
This custom FastMCP server running in Snowpark Container Services (SPCS) acts as the **Identity & Authorization Broker** sitting between Azure AI Foundry / Microsoft Entra ID and Snowflake Cortex Agents / Governance.

```
┌────────────────────────┐      Bearer <Entra_JWT>      ┌──────────────────────────────────────────────┐
│ Azure AI Foundry Agent │ ───────────────────────────▶ │ FastMCP Identity Broker (Python SPCS Service)│
│  (e.g., Entra User)    │   + Snowflake Ingress Token  │                                              │
└────────────────────────┘                              │  1. Parse/Decode Entra Token (upn/email)     │
                                                        │  2. Lookup ENTRA_USER_MAP in Snowflake       │
                                                        │  3. Connect via Persona RSA Key-Pair         │
                                                        └──────────────────────┬───────────────────────┘
                                                                               │ Exec as Mapped Persona
                                                                               ▼
                                                        ┌──────────────────────────────────────────────┐
                                                        │ Snowflake Horizon Data Governance & Engine   │
                                                        │                                              │
                                                        │  • Row Access Policy (RAP_PARK_SCOPE)        │
                                                        │  • Column Masking Policies (MP_MASK_*)       │
                                                        │  • Cortex Retrieval Agent Authorization     │
                                                        │  • Query History & Audit Attribution         │
                                                        └──────────────────────────────────────────────┘
```

---

## Key Talking Points for Pedro & Aaron

1. **Why standard MCP isn't enough (Pedro's Point):**
   - Standard MCP servers use a single shared credential for all requests, blinding Snowflake to the real human user.
   - Built-in External OAuth requires 1:1 user mapping and requires every MCP client tool to implement complex interactive token exchanges.

2. **How our Custom SPCS FastMCP Broker solves it:**
   - **Programmatic Mapping:** Python middleware extracts the Entra identity claim (`upn`/`email`), and matches it against `ENTRA_USER_MAP`.
   - **Zero Shared Data Credential:** The SPCS service connects to Snowflake dynamically as the resolved user (`MCP_POC_CEO` vs `MCP_POC_ANALYST`) using key-pair authentication.
   - **True Governance & Policy Enforcement:** Snowflake applies row-level security and column masking directly during query compilation.
   - **Complete Audit Trail:** Every query is tagged with both the upstream Entra ID (`ceo@amusementpark.com`) and the Snowflake mapped user in `SNOWFLAKE.INFORMATION_SCHEMA.QUERY_HISTORY`.
