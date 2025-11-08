import React from 'react'

function SourcePanel({ sources, usedDocuments }) {
  const safeSources = Array.isArray(sources) ? sources.slice(0, 3) : []

  return (
    <div className="source-panel">
      <h3>Sources</h3>
      <div className="source-list">
        {safeSources.length > 0 ? (
          <>
            {!usedDocuments && (
              <div className="source-notice">
                Using general maintenance knowledge. Upload documents in the admin panel for specific guidance.
              </div>
            )}
            {safeSources.map((source, idx) => (
              <div key={idx} className="source-item">
                <div className="source-doc">{source.doc || 'Unknown'}</div>
                <div className="source-excerpt">
                  {source.excerpt || 'No excerpt available'}
                </div>
              </div>
            ))}
          </>
        ) : (
          <div className="empty-state">
            No sources available. Upload maintenance documents via the admin panel.
          </div>
        )}
      </div>
    </div>
  )
}

export default SourcePanel
