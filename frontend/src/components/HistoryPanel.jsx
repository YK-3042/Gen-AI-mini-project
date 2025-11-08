import React from "react";

function HistoryPanel({ history, onSelectQuery }) {
  const safeHistory = Array.isArray(history) ? history : [];

  const handleDelete = async (id, query) => {
    if (window.confirm(`Delete this entry?\n\n"${query}"`)) {
      try {
        const response = await fetch(`${API_BASE}/history/${id}`, {
          method: "DELETE",
        });

        if (response.ok) {
          alert("Entry deleted successfully.");
          window.location.reload();
        } else {
          const errorData = await response.json();
          alert(`Failed to delete: ${errorData.detail || "Unknown error"}`);
        }
      } catch (error) {
        console.error("Delete error:", error);
        alert("Error: Could not connect to backend.");
      }
    }
  };

  return (
    <div className="history-panel">
      <h3>Recent Queries</h3>
      <div className="history-list">
        {safeHistory.length > 0 ? (
          safeHistory.map((item) => (
            <div
              key={item.id}
              className="history-item"
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
              }}
            >
              <div
                onClick={() => onSelectQuery(item.query)}
                role="button"
                tabIndex={0}
                aria-label={`Load query: ${item.query}`}
                style={{ flexGrow: 1, cursor: "pointer" }}
              >
                <div className="history-query">{item.query}</div>
                <div className="history-date">
                  {new Date(item.created_at).toLocaleDateString()}
                </div>
              </div>

              <button
                onClick={(e) => {
                  e.stopPropagation();
                  handleDelete(item.id, item.query);
                }}
                style={{
                  background: "transparent",
                  border: "none",
                  color: "#ff4d4f",
                  cursor: "pointer",
                  fontSize: "16px",
                  marginLeft: "8px",
                }}
                title="Delete this entry"
              >
                🗑️
              </button>
            </div>
          ))
        ) : (
          <div className="empty-state">No history yet</div>
        )}
      </div>
    </div>
  );
}

export default HistoryPanel;
