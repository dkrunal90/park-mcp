# 🚀 UI Demo Quick Start

## Overview

A beautiful React dashboard demonstrating the MCP server with role-based access control in action. Switch between CEO and Analyst personas to see how RBAC gates data access.

## Prerequisites

- Node.js 16+ installed
- MCP server deployed and running
- Valid PATs in `.env` (CEO_PAT and ANALYST_PAT)

## 1-Minute Setup

```bash
# Navigate to UI folder
cd ui

# Install dependencies
npm install

# Start both backend and frontend
npm run dev
```

Open **http://localhost:3000** in your browser.

## What You'll See

### CEO Persona Demo
1. Click **👔 CEO** button
2. Click **🔐 Identity Check** → See `ceo@amusementpark.com → MCP_POC_CEO / PARK_CEO`
3. Click **💰 Financial Summary** → See **3 parks** + **10 GL departments** ✅
4. Type a question and click **🧠 Cortex Query** → E.g., "What is ticket revenue?" → Sees full data ✅

### Analyst Persona Demo
1. Click **📊 Analyst** button
2. Click **🔐 Identity Check** → See `analyst@amusementpark.com → MCP_POC_ANALYST / PARK_ANALYST`
3. Click **💰 Financial Summary** → See **only Mountain Peaks** + GL access **denied** ✅
4. Click **🧠 Cortex Query** → Cannot access financial queries (proper RBAC) ✅

## Key Features

| Feature | CEO | Analyst |
|---------|-----|---------|
| View all 3 parks | ✅ | ❌ (Mountain Peaks only) |
| Access GL departments | ✅ | ❌ (RBAC blocked) |
| Query revenue data | ✅ | ❌ (Cortex role-restricted) |
| Identity verification | ✅ | ✅ |

## File Structure

```
ui/
├── backend.js              # Express server proxying MCP
├── package.json            # Dependencies & scripts
├── vite.config.js          # Vite + proxy config
├── index.html              # HTML template
├── src/
│   ├── App.jsx            # Main React component
│   ├── App.css            # Styling (dark mode)
│   ├── main.jsx           # Entry point
│   └── components/
│       ├── PersonaSelector.jsx    # Persona switcher
│       ├── ToolExecutor.jsx       # Tool buttons
│       └── Results.jsx            # Response formatter
└── README.md              # Full documentation
```

## Commands

```bash
npm run dev                 # Frontend + Backend
npm run dev:frontend        # Frontend only (port 3000)
npm run dev:backend         # Backend only (port 5000)
npm run build              # Production build
npm run preview            # Preview build
```

## Architecture

```
Browser (React)
    ↓
Backend Proxy (Express:5000)
    ↓ Injects PAT + Headers
MCP Server (SPCS:8080)
    ↓
Snowflake (Governance)
    ↓ RBAC/RAP enforcement
Results ← Filtered by role
```

## Troubleshooting

**"Cannot connect to backend"**
- Start backend: `npm run dev:backend`
- Check port 5000 is available

**"PAT is invalid"**
- Verify PATs in `../.env` are correct
- Check tokens aren't expired

**"Slow responses"**
- Cortex queries take 20-30 seconds (normal)
- Check MCP server logs

## Next Steps

- View [full UI documentation](./ui/README.md)
- Explore [MCP Server docs](./DEPLOYMENT.md)
- Check [API responses](./PROJECT_STORY.md) for technical details

## Live Demo Flow

**Perfect for demo purposes:**

1. **Show Identity Mapping** → Run `whoami` for both personas
2. **Show RBAC Enforcement** → Run `get_financial_summary` to see filtering
3. **Show Cortex Integration** → Run `ask_park_insights` queries
4. **Highlight Access Denied** → Show Analyst getting blocked from GL data

---

**Demo Duration:** ~5 minutes  
**Impact:** Demonstrates complete governance stack in action
