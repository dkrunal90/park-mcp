import express from 'express'
import cors from 'cors'
import axios from 'axios'
import dotenv from 'dotenv'
import path from 'path'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
dotenv.config({ path: path.join(__dirname, '..', '.env') })

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

  console.log(`[${persona}] Executing tool: ${toolName}`)
  console.log(`PAT available: ${!!personaConfig.pat}`)
  console.log(`API Key available: ${!!process.env.MCP_API_KEY}`)

  const headers = {
    'Authorization': `Snowflake Token="${personaConfig.pat}"`,
    'X-API-Key': process.env.MCP_API_KEY || '123456',
    'X-Entra-User': personaConfig.email,
    'Content-Type': 'application/json',
    'Accept': 'application/json, text/event-stream'
  }

  const jsonRpcBody = {
    jsonrpc: '2.0',
    id: 1,
    method: 'tools/call',
    params: {
      name: toolName,
      arguments: question ? { question } : {}
    }
  }

  try {
    console.log(`Calling MCP: POST ${MCP_BASE_URL}`)
    const response = await axios.post(MCP_BASE_URL, jsonRpcBody, { 
      headers, 
      timeout: 60000,
      validateStatus: () => true // Don't throw on any status code
    })
    
    console.log(`Response status: ${response.status}`)
    
    // Parse response - handle both streamed and regular JSON responses
    let data = response.data
    if (typeof data === 'string' && data.includes('data: ')) {
      data = data.split('data: ').pop()
    }
    
    if (typeof data === 'string') {
      data = JSON.parse(data)
    }
    
    if (response.status === 200 && data.result) {
      return data.result
    }
    
    return {
      error: true,
      status: response.status,
      detail: data.error?.message || data.detail || JSON.stringify(data).substring(0, 300)
    }
  } catch (error) {
    console.error(`Error executing ${toolName}:`, error.message)
    return {
      error: true,
      detail: error.message || 'Network error connecting to MCP server'
    }
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
