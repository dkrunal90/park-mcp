import React, { useState } from 'react'
import './App.css'
import PersonaSelector from './components/PersonaSelector'
import ToolExecutor from './components/ToolExecutor'
import Results from './components/Results'

function App() {
  const [selectedPersona, setSelectedPersona] = useState('ceo')
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(false)

  const personas = {
    ceo: {
      name: 'CEO',
      email: 'ceo@amusementpark.com',
      role: 'PARK_CEO',
      color: '#8b5cf6',
      description: 'Full access to all parks and financial data'
    },
    analyst: {
      name: 'Analyst',
      email: 'analyst@amusementpark.com',
      role: 'PARK_ANALYST',
      color: '#06b6d4',
      description: 'Restricted to Mountain Peaks park only'
    }
  }

  const handleExecuteTool = async (tool, question = null) => {
    setLoading(true)
    const startTime = Date.now()

    try {
      const payload = {
        persona: selectedPersona,
        tool,
        ...(question && { question })
      }

      const response = await fetch('/api/execute-tool', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })

      const data = await response.json()
      const duration = Date.now() - startTime

      setResults(prev => [{
        tool,
        persona: selectedPersona,
        timestamp: new Date().toLocaleTimeString(),
        duration,
        status: response.ok ? 'success' : 'error',
        data
      }, ...prev])
    } catch (error) {
      setResults(prev => [{
        tool,
        persona: selectedPersona,
        timestamp: new Date().toLocaleTimeString(),
        status: 'error',
        error: error.message
      }, ...prev])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-content">
          <h1>🎢 Amusement Park MCP Server Demo</h1>
          <p>Interactive demonstration of role-based access control with Snowflake + Azure Foundry</p>
        </div>
      </header>

      <div className="app-container">
        <aside className="sidebar">
          <PersonaSelector
            personas={personas}
            selectedPersona={selectedPersona}
            onSelectPersona={setSelectedPersona}
          />
        </aside>

        <main className="main-content">
          <section className="info-panel">
            <div className="persona-info" style={{ borderLeft: `4px solid ${personas[selectedPersona].color}` }}>
              <h2>{personas[selectedPersona].name} Persona</h2>
              <p className="email">{personas[selectedPersona].email}</p>
              <p className="role">Role: {personas[selectedPersona].role}</p>
              <p className="description">{personas[selectedPersona].description}</p>
            </div>
          </section>

          <section className="tools-panel">
            <ToolExecutor
              onExecuteTool={handleExecuteTool}
              loading={loading}
              persona={selectedPersona}
            />
          </section>

          <section className="results-panel">
            <Results results={results} />
          </section>
        </main>
      </div>
    </div>
  )
}

export default App
