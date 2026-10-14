# 🎢 Park MCP UI Demo

Interactive React dashboard to demonstrate the Model Context Protocol (MCP) server with role-based access control.

## Features

✅ **Dual Persona Demo**
- CEO: Full access to all parks and financial data
- Analyst: Restricted to Mountain Peaks park only

✅ **Three Interactive Tools**
1. **Identity Check** - Verify user mapping (Entra ID → Snowflake)
2. **Financial Summary** - View park revenue and GL data (role-filtered)
3. **Cortex Query** - Ask natural language questions about park data

✅ **Real-time Response Display**
- Execution duration tracking
- Formatted JSON output
- RBAC enforcement visualization
- Error handling

✅ **Beautiful Dark-Mode UI**
- Modern gradient design
- Responsive layout
- Smooth animations

## Setup

### Prerequisites
- Node.js 16+ installed
- MCP server running at: `https://abz2pr-tqmttqp-hw26207.snowflakecomputing.app/mcp`
- Valid PATs in `.env` file (one level up from `/ui`)

### Installation

```bash
cd ui
npm install
```

### Environment Configuration

The UI backend reads PATs from `../.env`. Ensure these are set:

```env
CEO_PAT=eyJraWQiOiI3NTE0MDA4MzcxNyIsImFsZyI6IkVTMjU2In0.eyJ...
ANALYST_PAT=eyJraWQiOiI3NTE0MDA4MzcxNyIsImFsZyI6IkVTMjU2In0.eyJ...
MCP_API_KEY=123456
```

### Running the UI

**Development Mode** (runs both frontend and backend):
```bash
npm run dev
```

This starts:
- Frontend: http://localhost:3000
- Backend: http://localhost:5000

**Backend Only** (if frontend is served separately):
```bash
npm run dev:backend
```

**Production Build**:
```bash
npm run build
npm run preview
```

## Architecture

```
┌─────────────────────────────────┐
│   React Frontend (Port 3000)     │
│  ┌─────────────────────────────┐ │
│  │  PersonaSelector            │ │
│  │  ToolExecutor               │ │
│  │  Results Display            │ │
│  └─────────────────────────────┘ │
└──────────────┬────────────────────┘
               │ HTTP/JSON
┌──────────────▼────────────────────┐
│  Express Backend (Port 5000)      │
│  • Proxy to MCP server            │
│  • Inject PATs & headers          │
│  • Error handling                 │
└──────────────┬────────────────────┘
               │ HTTPS Bearer Token
┌──────────────▼────────────────────────────────────────┐
│  MCP Server (SPCS Public Endpoint)                   │
│  https://abz2pr-tqmttqp-hw26207.snowflakecomputing... │
│  • Tool execution: whoami, get_financial_summary    │
│  • NLP: ask_park_insights (Cortex Agent)            │
│  • RBAC: Row Access Policies, Column Masking        │
└───────────────────────────────────────────────────────┘
```

## Usage

1. **Select a Persona** - Click CEO or Analyst in the sidebar
2. **Execute a Tool**:
   - Click "Identity Check" to verify user mapping
   - Click "Financial Summary" to see role-filtered data
   - Type a question and click "Cortex Query" for NL queries
3. **View Results** - Responses appear with timing and status

### CEO Demo (Full Access)
- Sees all 3 parks: Bayou Boardwalk, Golden Coast, Mountain Peaks
- Accesses all 10 GL departments
- Can query ticket revenue across all parks

### Analyst Demo (Restricted Access)
- Sees only Mountain Peaks park
- GL department access denied (RBAC)
- Cortex queries limited to non-financial datasets

## Error Handling

The UI gracefully handles:
- ❌ Invalid/expired PATs → 401 Unauthorized
- ❌ Missing API-Key → 401 Unauthorized
- ❌ Unauthorized data access → 403 with details
- ❌ Network timeouts → Error message with correlation ID

## File Structure

```
ui/
├── package.json           # Dependencies & scripts
├── vite.config.js        # Vite config with proxy
├── backend.js            # Express server & MCP proxy
├── index.html            # HTML template
├── src/
│   ├── main.jsx          # React entry point
│   ├── App.jsx           # Main app component
│   ├── App.css           # Global styles
│   └── components/
│       ├── PersonaSelector.jsx   # Persona switch
│       ├── ToolExecutor.jsx      # Tool buttons & input
│       └── Results.jsx           # Result formatting
└── README.md             # This file
```

## API Endpoints

### Backend Proxy

**POST** `/api/execute-tool`
```json
{
  "persona": "ceo|analyst",
  "tool": "whoami|get_financial_summary|ask_park_insights",
  "question": "Optional question for ask_park_insights"
}
```

**Response**:
```json
{
  "entra_user_identity": "...",
  "snowflake_mapped_user": "...",
  "query_id": "...",
  "correlation_id": "...",
  ...
}
```

**GET** `/api/health`
- Returns backend status and MCP endpoint URL

## Troubleshooting

### "Programmatic access token is invalid"
- Check PATs in `../.env` are correct and not expired
- Verify Snowflake tokens are properly generated for users

### "Connection refused" to backend
- Ensure backend is running: `npm run dev:backend`
- Check port 5000 is available

### CORS errors
- Backend has CORS enabled for all origins (dev only)
- For production, restrict origin to your domain

### Slow Cortex queries
- Cortex Agent queries can take 20-30 seconds
- Check MCP server logs for query execution details

## Development

### Adding New Tools

1. Add tool to `ToolExecutor.jsx` tools array:
```jsx
{
  id: 'new_tool',
  name: 'Tool Display Name',
  description: 'What it does',
  icon: '📊'
}
```

2. Update `backend.js` to handle the new tool
3. Format output in `Results.jsx` formatOutput function

### Styling

Global styles in `App.css` use CSS Grid and Flexbox. Color scheme:
- **Purple** (#8b5cf6) - CEO persona
- **Cyan** (#06b6d4) - Analyst persona
- **Dark Background** (#0f172a, #1e293b) - Slate-900

### Hot Reload

Both frontend and backend support hot reload:
- Frontend: Vite HMR on port 3000
- Backend: Automatically restarts on file changes

## Performance

- **Frontend bundle**: ~150KB (minified)
- **Tool execution**: 0.2s to 30s depending on tool
- **Network latency**: ~200ms to SPCS endpoint

## Security Notes

⚠️ **This is a DEMO only**
- PATs stored in `.env` (dev convenience)
- No authentication on frontend
- CORS open to all origins

**For production**:
- Use secure vaults (Secrets Manager, Key Vault)
- Implement OAuth2 on frontend
- Restrict CORS to trusted origins
- Enable HTTPS everywhere

## License

Same as parent project (Park-MCP)

## Support

For issues, check:
1. MCP server status: Visit the endpoint in browser
2. Backend logs: `npm run dev:backend` console output
3. Network tab: Browser DevTools F12
4. Correlation ID: Found in all responses for Snowflake query tracking
