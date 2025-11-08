import React, { useState, useRef, useEffect } from 'react'

function ChatBox({ messages, onSendMessage, isLoading }) {
  const [input, setInput] = useState('')
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSubmit = (e) => {
    e.preventDefault()
    if (input.trim() && !isLoading) {
      onSendMessage(input.trim())
      setInput('')
    }
  }

  return (
    <div className="chat-box">
      <div className="messages-container">
        {messages && Array.isArray(messages) && messages.length > 0 ? (
          messages.map((msg, idx) => (
            <div key={idx} className={`message ${msg.type}`}>
              <div className="message-label">{msg.type === 'user' ? 'You' : 'Assistant'}</div>
              <div className="message-content">{msg.content}</div>
            </div>
          ))
        ) : (
          <div className="welcome-message">
            <h2>Welcome to Maintenance Query Agent</h2>
            <p>Ask any maintenance-related question to get started.</p>
          </div>
        )}
        {isLoading && (
          <div className="message assistant">
            <div className="message-label">Assistant</div>
            <div className="message-content">
              <span className="typing-indicator">Thinking...</span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
      
      <form onSubmit={handleSubmit} className="input-form">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask a maintenance question..."
          disabled={isLoading}
          aria-label="Chat input"
          className="chat-input"
        />
        <button
          type="submit"
          disabled={isLoading || !input.trim()}
          className="send-button"
          aria-label="Send message"
        >
          {isLoading ? 'Sending...' : 'Send'}
        </button>
      </form>
    </div>
  )
}

export default ChatBox
