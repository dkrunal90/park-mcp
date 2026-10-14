import React from 'react'

export default function PersonaSelector({ personas, selectedPersona, onSelectPersona }) {
  return (
    <div className="persona-selector">
      <h3 style={{ marginBottom: '1rem', color: '#e2e8f0' }}>Select Persona</h3>
      {Object.entries(personas).map(([key, persona]) => (
        <button
          key={key}
          className={`persona-btn ${selectedPersona === key ? 'active' : ''} ${key === 'analyst' ? 'analyst' : ''}`}
          onClick={() => onSelectPersona(key)}
        >
          <div style={{ fontSize: '1.2rem', marginBottom: '0.25rem' }}>
            {key === 'ceo' ? '👔' : '📊'} {persona.name}
          </div>
          <div style={{ fontSize: '0.75rem', opacity: 0.7 }}>{persona.email}</div>
        </button>
      ))}
    </div>
  )
}
