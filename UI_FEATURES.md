# 🎢 React UI Demo - Complete Feature Guide

## What's Included

A **production-ready React dashboard** that provides an interactive way to demo the MCP server's capabilities and governance stack.

## Key Components

### 1. Persona Switcher 👥
- **CEO** (Purple) - Full access to all data
- **Analyst** (Cyan) - Restricted access by RBAC

### 2. Three Interactive Tools 🛠️
- **Identity Check** - Verify user mapping (Entra ID → Snowflake)
- **Financial Summary** - View role-filtered park & GL data
- **Cortex Query** - Ask natural language questions

### 3. Real-Time Results Display 📊
- Execution timing in milliseconds
- Formatted JSON responses
- Correlation IDs for audit tracking
- Success/error indicators

### 4. Beautiful Dark-Mode UI 🎨
- Modern gradient design
- Smooth animations
- Responsive layout
- Syntax-highlighted output

## Demo Flow

```
1. Select Persona (CEO or Analyst)
   ↓
2. Click a Tool Button
   ↓
3. See instant response with formatting
   ↓
4. Compare CEO vs Analyst access levels
```

## Getting Started

```bash
cd ui
npm install
npm run dev
```

Visit http://localhost:3000 in your browser.

## File Structure

```
ui/
├── backend.js           - Express proxy server
├── package.json         - Dependencies
├── vite.config.js       - Vite config
├── index.html          - HTML template
├── src/
│   ├── App.jsx        - Main component
│   ├── App.css        - Styling
│   ├── main.jsx       - Entry point
│   └── components/
│       ├── PersonaSelector.jsx
│       ├── ToolExecutor.jsx
│       └── Results.jsx
└── README.md          - Full documentation
```

## What Each Tool Shows

### 🔐 Identity Check
**CEO Response:**
```
Entra: ceo@amusementpark.com
SF User: MCP_POC_CEO
Role: PARK_CEO
```

**Analyst Response:**
```
Entra: analyst@amusementpark.com
SF User: MCP_POC_ANALYST
Role: PARK_ANALYST
```

### 💰 Financial Summary
**CEO:** 
- 3 parks visible ✅
- 10 GL departments accessible ✅

**Analyst:**
- 1 park visible (Mountain Peaks) ✅
- GL access denied ❌

### 🧠 Cortex Query
**CEO:** Can ask "What is ticket revenue?" → Gets answer ✅

**Analyst:** Same query → Access denied ❌

## Technical Stack

- **Frontend:** React 18 + Vite
- **Backend:** Express.js (PAT proxy)
- **Styling:** CSS (dark mode)
- **Communication:** REST API (JSON)

## Performance

| Tool | Time |
|------|------|
| whoami | ~2-3s |
| Financial Summary | ~6-7s |
| Cortex Query | ~20-30s |

## Perfect For

- 🎤 Live demonstrations
- 👥 Team onboarding
- 📋 Governance showcase
- ✅ RBAC validation
- 🏆 Sales demos

## Security Notes

**Development:**
- PATs in `.env` (convenient)
- No authentication (demo mode)

**Production:**
- Use Secrets Manager
- Implement OAuth2
- Restrict CORS
- Enable HTTPS

## Troubleshooting

**Backend won't start?**
```bash
npm run dev:backend
```

**"PAT is invalid"?**
Check that `../.env` has valid tokens

**Slow responses?**
Cortex queries take 20-30s (normal)

---

See [UI Quick Start](./UI_QUICKSTART.md) for setup instructions.
