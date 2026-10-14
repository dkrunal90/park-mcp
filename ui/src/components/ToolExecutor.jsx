import React, { useState } from 'react'

export default function ToolExecutor({ onExecuteTool, loading, persona }) {
  const [question, setQuestion] = useState('')

  const tools = [
    {
      id: 'whoami',
      name: 'Identity Check',
      description: 'Verify current user identity and role',
      icon: '🔐'
    },
    {
      id: 'get_financial_summary',
      name: 'Financial Summary',
      description: 'Get park revenue and GL data (role-filtered)',
      icon: '💰'
    },
    {
      id: 'ask_park_insights',
      name: 'Cortex Query',
      description: 'Ask natural language questions about park data',
      icon: '🧠',
      needsInput: true
    }
  ]

  const handleExecute = (toolId) => {
    if (toolId === 'ask_park_insights' && question.trim()) {
      onExecuteTool(toolId, question)
      setQuestion('')
    } else if (toolId !== 'ask_park_insights') {
      onExecuteTool(toolId)
    }
  }

  return (
    <div>
      <h3>Available Tools</h3>
      <div className="tools-grid">
        {tools.map(tool => (
          <div key={tool.id}>
            <button
              className="tool-btn"
              onClick={() => handleExecute(tool.id)}
              disabled={loading || (tool.needsInput && !question.trim())}
              title={tool.description}
            >
              {loading && tool.needsInput === false ? (
                <span className="loading-spinner"></span>
              ) : (
                <span>{tool.icon}</span>
              )}
              {tool.name}
            </button>
            {tool.needsInput && (
              <input
                type="text"
                className="question-input"
                placeholder="Ask something... (e.g., 'What is the ticket revenue?')"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleExecute(tool.id)}
                disabled={loading}
              />
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
