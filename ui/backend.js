import express from 'express'
import cors from 'cors'
import axios from 'axios'
import dotenv from 'dotenv'

dotenv.config('../.env')

const app = express()
const PORT = process.env.UI_BACKEND_PORT || 5000

app.use(cors())
app.use(express.json())

const MCP_BASE_URL = 'https://abz2pr-tqmttqp-hw26207.snowflakecomputing.app/mcp'

const personas = {
  ceo: {
    pat: process.env.CEO_PAT,
    email: 'ceo@amusementpark.com'
  },
  analyst: {
    pat: process.env.ANALYST_PAT,
    email: 'analyst@amusementpark.com'
  }
}

async function executeTool(toolName, persona, question = null) {
  const personaConfig = personas[persona]
  if (!personaConfig) throw new Error(`Unknown persona: ${persona}`)

  const headers = {
    'Snowflake-Token': `Bearer ${personaConfig.pat}`,
    'X-API-Key': process.env.MCP_API_KEY || '123456',
    'X-Entra-User': personaConfig.email,
    'Content-Type': 'application/json'
  }

  try {
    const response = await axios.post(
      `${MCP_BASE_URL}/call`,
      {
        name: toolName,
        arguments: question ? { question } : {}
      },
      { headers, timeout: 60000 }
    )
    return response.data
  } catch (error) {
    if (error.response) {
      return {
        error: true,
        status: error.response.status,
        detail: error.response.data?.detail || error.message
      }
    }
    throw error
  }
}

app.post('/api/execute-tool', async (req, res) => {
  try {
    const { persona, tool, question } = req.body

    if (!persona || !tool) {
      return res.status(400).json({ error: 'Missing persona or tool' })
    }

    const result = await executeTool(tool, persona, question)
    res.json(result)
  } catch (error) {
    console.error('Tool execution error:', error.message)
    res.status(500).json({
      error: true,
      detail: error.message
    })
  }
})

app.get('/api/health', (req, res) => {
  res.json({ status: 'ok', mcp_endpoint: MCP_BASE_URL })
})

app.listen(PORT, () => {
  console.log(`🚀 UI Backend running on http://localhost:${PORT}`)
  console.log(`📡 MCP Server: ${MCP_BASE_URL}`)
})
