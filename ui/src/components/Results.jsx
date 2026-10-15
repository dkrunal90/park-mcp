import React from 'react'

export default function Results({ results }) {
  return (
    <div>
      <h3>Results</h3>
      {results.length === 0 ? (
        <div className="no-results">
          <p>Execute a tool to see results here</p>
        </div>
      ) : (
        <div className="results-list">
          {results.map((result, idx) => (
            <div
              key={idx}
              className={`result-item ${result.persona} ${result.status === 'error' ? 'error' : ''}`}
            >
              <div className="result-header">
                <span className="result-tool">
                  {result.tool.replace(/_/g, ' ').toUpperCase()}
                </span>
                <span className="result-meta">
                  <span>{result.timestamp}</span>
                  {result.duration && (
                    <span className="result-duration">{result.duration}ms</span>
                  )}
                  <span className="result-status">
                    {result.status === 'error' ? '❌' : '✅'}
                  </span>
                </span>
              </div>

              {result.error ? (
                <div className="result-data result-error">
                  {result.error}
                </div>
              ) : (
                <div className="result-data">
                  {formatOutput(result.data)}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function formatOutput(data) {
  // Handle string responses
  if (typeof data === 'string') {
    return <div style={{ lineHeight: '1.6', color: '#e2e8f0', fontSize: '1rem' }}>{data}</div>
  }

  // Handle errors
  if (data.error) {
    return (
      <div style={{ color: '#f87171', fontSize: '1rem', lineHeight: '1.6' }}>
        <strong>⚠️ Error:</strong> {data.detail}
      </div>
    )
  }

  if (data.detail) {
    return <div style={{ color: '#f87171' }}>Error: {data.detail}</div>
  }

  // Format identity response (whoami) - Plain text
  if (data.snowflake_mapped_user) {
    return (
      <div style={{ lineHeight: '1.8', color: '#e2e8f0', fontSize: '1rem' }}>
        <p style={{ margin: '0.5rem 0' }}>
          User: <strong>{data.entra_user_identity}</strong>
        </p>
        <p style={{ margin: '0.5rem 0' }}>
          Role: <strong>{data.snowflake_mapped_role}</strong>
        </p>
        <p style={{ margin: '0.5rem 0', color: '#94a3b8', fontSize: '0.9rem' }}>
          (ID: {data.correlation_id})
        </p>
      </div>
    )
  }

  // Format financial summary - Plain text only
  if (data.ticket_revenue_by_park) {
    const hasGLData = Array.isArray(data.gl_actual_vs_budget_by_department)
    const glDenied = typeof data.gl_actual_vs_budget_by_department === 'string'
    
    return (
      <div style={{ lineHeight: '1.8', color: '#e2e8f0', fontSize: '1rem' }}>
        <p style={{ margin: '1rem 0 0.5rem 0', fontWeight: 'bold' }}>Parks Accessible:</p>
        {data.ticket_revenue_by_park.map((park, i) => (
          <p key={i} style={{ margin: '0.3rem 0', marginLeft: '1rem' }}>
            • {park.PARK_NAME}: ${parseFloat(park.TICKET_NET_REVENUE).toLocaleString('en-US', { maximumFractionDigits: 0 })}
          </p>
        ))}

        {glDenied && (
          <>
            <p style={{ margin: '1rem 0 0.5rem 0', fontWeight: 'bold', color: '#f87171' }}>Financial Departments:</p>
            <p style={{ margin: '0.3rem 0', marginLeft: '1rem', color: '#f87171' }}>✗ Access Denied (Role-Based Access Control enforced)</p>
          </>
        )}

        {hasGLData && (
          <>
            <p style={{ margin: '1rem 0 0.5rem 0', fontWeight: 'bold' }}>Department Budgets (Sample):</p>
            {data.gl_actual_vs_budget_by_department.slice(0, 5).map((dept, i) => (
              <p key={i} style={{ margin: '0.3rem 0', marginLeft: '1rem' }}>
                • {dept.DEPARTMENT_NAME}: Actual ${parseFloat(dept.ACTUAL).toLocaleString('en-US', { maximumFractionDigits: 0 })} vs Budget ${parseFloat(dept.BUDGET).toLocaleString('en-US', { maximumFractionDigits: 0 })}
              </p>
            ))}
            {data.gl_actual_vs_budget_by_department.length > 5 && (
              <p style={{ margin: '0.5rem 0', marginLeft: '1rem', fontSize: '0.9rem', color: '#94a3b8' }}>
                ... plus {data.gl_actual_vs_budget_by_department.length - 5} more departments
              </p>
            )}
          </>
        )}
      </div>
    )
  }

  // Format Cortex/AI answers - Plain text
  if (data.answer) {
    return (
      <div style={{ lineHeight: '1.8', color: '#e2e8f0', fontSize: '1rem' }}>
        <p style={{ margin: '0.5rem 0', color: '#fbbf24', fontWeight: 'bold' }}>Answer:</p>
        <p style={{ margin: '0.5rem 0', whiteSpace: 'pre-wrap' }}>{data.answer}</p>
      </div>
    )
  }

  // Fallback for any other structured content - extract text only
  if (data.content && Array.isArray(data.content)) {
    return (
      <div style={{ lineHeight: '1.8', color: '#e2e8f0', fontSize: '1rem' }}>
        {data.content.map((item, i) => (
          <p key={i} style={{ margin: '0.5rem 0' }}>
            {item.text || JSON.stringify(item)}
          </p>
        ))}
      </div>
    )
  }

  // Last resort - show minimal info
  return (
    <div style={{ lineHeight: '1.6', color: '#e2e8f0', fontSize: '1rem' }}>
      <p>Data received successfully</p>
    </div>
  )
}
