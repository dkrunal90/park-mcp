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
  if (typeof data === 'string') {
    return data
  }

  if (data.detail) {
    return `Error: ${data.detail}`
  }

  if (data.answer) {
    return (
      <>
        <div style={{ marginBottom: '1rem', color: '#a5f3fc' }}>
          <strong>Q:</strong> {data.question || 'Natural Language Query'}
        </div>
        <div style={{ color: '#86efac' }}>
          <strong>A:</strong> {data.answer}
        </div>
      </>
    )
  }

  // Format financial summary
  if (data.ticket_revenue_by_park) {
    return (
      <>
        <div style={{ marginBottom: '1rem' }}>
          <strong style={{ color: '#fbbf24' }}>Parks (Visible to User):</strong>
          <ul style={{ marginTop: '0.5rem', marginLeft: '1rem', color: '#a5f3fc' }}>
            {data.ticket_revenue_by_park.map((park, i) => (
              <li key={i}>
                {park.PARK_NAME}: ${parseFloat(park.TICKET_NET_REVENUE).toLocaleString('en-US', {
                  minimumFractionDigits: 2
                })}
              </li>
            ))}
          </ul>
        </div>
        {data.gl_actual_vs_budget_by_department && !data.gl_actual_vs_budget_by_department.includes && (
          <div>
            <strong style={{ color: '#fbbf24' }}>GL Departments (Accessible):</strong>
            <ul style={{ marginTop: '0.5rem', marginLeft: '1rem', color: '#a5f3fc' }}>
              {data.gl_actual_vs_budget_by_department.slice(0, 5).map((dept, i) => (
                <li key={i}>
                  {dept.DEPARTMENT_NAME}: ${parseFloat(dept.ACTUAL).toLocaleString()} / ${parseFloat(dept.BUDGET).toLocaleString()}
                </li>
              ))}
              {data.gl_actual_vs_budget_by_department.length > 5 && (
                <li>... and {data.gl_actual_vs_budget_by_department.length - 5} more</li>
              )}
            </ul>
          </div>
        )}
        {typeof data.gl_actual_vs_budget_by_department === 'string' && (
          <div style={{ color: '#f87171' }}>
            <strong>GL Access:</strong> {data.gl_actual_vs_budget_by_department}
          </div>
        )}
      </>
    )
  }

  // Format identity response
  if (data.snowflake_mapped_user) {
    return (
      <>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
          <div>
            <strong style={{ color: '#fbbf24' }}>Entra User:</strong>
            <div style={{ color: '#a5f3fc' }}>{data.entra_user_identity}</div>
          </div>
          <div>
            <strong style={{ color: '#fbbf24' }}>SF User:</strong>
            <div style={{ color: '#a5f3fc' }}>{data.snowflake_mapped_user}</div>
          </div>
          <div>
            <strong style={{ color: '#fbbf24' }}>SF Role:</strong>
            <div style={{ color: '#86efac' }}>{data.snowflake_mapped_role}</div>
          </div>
          <div>
            <strong style={{ color: '#fbbf24' }}>Correlation ID:</strong>
            <div style={{ color: '#a5f3fc', fontSize: '0.8rem' }}>
              {data.correlation_id}
            </div>
          </div>
        </div>
      </>
    )
  }

  return JSON.stringify(data, null, 2)
}
