import React, { useState } from 'react'

function LoginForm({ onLogin, error }) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (username && password) {
      setIsLoading(true)
      try {
        await onLogin(username, password)
      } finally {
        setIsLoading(false)
      }
    }
  }

  return (
    <div className="login-form-container">
      <form onSubmit={handleSubmit} className="login-form">
        <h2>Admin Login</h2>
        {error && <div className="error-message">{error}</div>}
        <div className="form-group">
          <label htmlFor="username">Username</label>
          <input
            type="text"
            id="username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            placeholder="Enter username"
            disabled={isLoading}
            aria-label="Username"
          />
        </div>
        <div className="form-group">
          <label htmlFor="password">Password</label>
          <input
            type="password"
            id="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Enter password"
            disabled={isLoading}
            aria-label="Password"
          />
        </div>
        <button type="submit" disabled={isLoading || !username || !password}>
          {isLoading ? 'Logging in...' : 'Login'}
        </button>
      </form>
    </div>
  )
}

export default LoginForm
