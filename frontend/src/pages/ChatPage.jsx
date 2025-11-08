import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import axios from "axios";
import ChatBox from "../components/ChatBox";
import HistoryPanel from "../components/HistoryPanel";
import SourcePanel from "../components/SourcePanel";

const API_BASE =
  window.location.hostname === "localhost"
    ? "http://localhost:8000"
    : `${window.location.protocol}//${window.location.hostname}:8000`.replace(
        ":5000",
        ":8000",
      );

function ChatPage() {
  const [messages, setMessages] = useState([]);
  const [history, setHistory] = useState([]);
  const [sources, setSources] = useState([]);
  const [usedDocuments, setUsedDocuments] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [healthStatus, setHealthStatus] = useState(null);
  const [healthError, setHealthError] = useState(false);

  useEffect(() => {
    checkHealth();
    loadHistory();
  }, []);

  const checkHealth = async () => {
    try {
      const response = await axios.get(`${API_BASE}/health`);
      setHealthStatus(response.data);
      setHealthError(false);
    } catch (error) {
      console.error("Health check failed:", error);
      setHealthError(true);
    }
  };

  const loadHistory = async () => {
    try {
      const response = await axios.get(`${API_BASE}/history?limit=20`);
      if (Array.isArray(response.data)) {
        setHistory(response.data);
      }
    } catch (error) {
      console.error("Failed to load history:", error);
    }
  };

  const handleSendMessage = async (query) => {
    const userMessage = { type: "user", content: query };
    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);

    try {
      const response = await axios.post(`${API_BASE}/chat`, { query });
      const data = response.data;

      const assistantMessage = { type: "assistant", content: data.answer };
      setMessages((prev) => [...prev, assistantMessage]);

      if (data.sources) {
        setSources(data.sources);
        setUsedDocuments(data.used_documents || false);
      }

      loadHistory();
    } catch (error) {
      console.error("Chat error:", error);
      const errorMessage = {
        type: "assistant",
        content:
          "Sorry, I encountered an error processing your request. Please try again.",
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSelectQuery = (query) => {
    handleSendMessage(query);
  };

  return (
    <div className="app-container">
      <header className="app-header">
        <h1>Maintenance Query Agent</h1>
        <div className="header-actions">
          {healthError ? (
            <button onClick={checkHealth} className="retry-button">
              Retry Health Check
            </button>
          ) : (
            healthStatus && (
              <div
                className={`health-indicator ${healthStatus.ok ? "healthy" : "unhealthy"}`}
              >
                {healthStatus.ok ? "● System OK" : "● System Error"}
              </div>
            )
          )}
          <Link to="/admin" className="admin-link">
            Admin Panel
          </Link>
        </div>
      </header>

      {healthError && (
        <div className="error-banner">
          Unable to connect to backend server. Please ensure the server is
          running.
        </div>
      )}

      <div className="main-content">
        {/* ✅ Updated to include setHistory */}
        <HistoryPanel
          history={history}
          onSelectQuery={handleSelectQuery}
          setHistory={setHistory}
        />
        <ChatBox
          messages={messages}
          onSendMessage={handleSendMessage}
          isLoading={isLoading}
        />
        <SourcePanel sources={sources} usedDocuments={usedDocuments} />
      </div>
    </div>
  );
}

export default ChatPage;
