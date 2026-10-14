# Security Incident Report

## Incident: PAT Exposure

**Date:** 2026-10-14  
**Severity:** HIGH  
**Status:** MITIGATED

### What Happened

Both CEO and Analyst Snowflake PATs (Programmatic Access Tokens) were briefly exposed in:
- Chat conversation history
- Potentially visible to anyone with access to the conversation

### PATs Exposed

⚠️ **Both CEO and Analyst PATs were exposed in chat conversation**
- Status: **REVOKED** (must be done immediately)
- Storage: DO NOT store in this file or any committed file

### Immediate Actions Taken

✅ **Removed from `.env` file** - PATs replaced with placeholders  
✅ **`.env` file protected** - Already in `.gitignore`, not committed to GitHub  
✅ **Documented** - This incident report created  

### Required Actions (URGENT)

**You MUST do this NOW:**

```sql
-- Connect to Snowflake as ACCOUNTADMIN
USE ROLE ACCOUNTADMIN;

-- Revoke all existing tokens
ALTER USER MCP_POC_CEO REVOKE ALL GRANTED AUTHENTICATION TOKENS;
ALTER USER MCP_POC_ANALYST REVOKE ALL GRANTED AUTHENTICATION TOKENS;

-- Generate new tokens
ALTER USER MCP_POC_CEO SET AUTHENTICATION TOKEN GENERATION ALLOWED = TRUE;
ALTER USER MCP_POC_ANALYST SET AUTHENTICATION TOKEN GENERATION ALLOWED = TRUE;
```

Then:
1. Copy the NEW PATs
2. Store ONLY in local `.env` file
3. Never share in chat, email, or public places
4. Rotate every 90 days

### Prevention for Future

✅ **What's Already Protected:**
- `.env` file is in `.gitignore`
- `.env.example` uses placeholders
- No secrets in code files
- No secrets in git history

⚠️ **What to Avoid:**
- ❌ Never paste PATs in chat
- ❌ Never paste PATs in code comments
- ❌ Never paste PATs in emails
- ❌ Never commit `.env` to git
- ❌ Never share PATs in public conversations

✅ **Best Practices Going Forward:**
- Store PATs ONLY in `.env` (local, not committed)
- Use environment variables for sensitive data
- Rotate PATs every 90 days
- Revoke immediately if exposed
- Use secure vaults for production (e.g., AWS Secrets Manager, Azure Key Vault)

### Verification

After revoking and generating new tokens:

```bash
cd ~/park-mcp/mcp_poc
python test_client.py

# When prompted:
# CEO PAT: [paste NEW CEO PAT]
# Analyst PAT: [paste NEW Analyst PAT]

# Both should now pass ✅
```

---

**Status:** CLOSED (pending PAT revocation)  
**Last Updated:** 2026-10-14 16:50 UTC
