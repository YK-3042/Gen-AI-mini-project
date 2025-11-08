import React, { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import axios from 'axios'
import LoginForm from '../components/LoginForm'

const API_BASE = window.location.hostname === 'localhost' 
  ? 'http://localhost:8000' 
  : `${window.location.protocol}//${window.location.hostname}:8000`.replace(':5000', ':8000')

function AdminPage() {
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [token, setToken] = useState(null)
  const [loginError, setLoginError] = useState('')
  const [documents, setDocuments] = useState([])
  const [uploadStatus, setUploadStatus] = useState('')
  const [isUploading, setIsUploading] = useState(false)
  
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [passwordMessage, setPasswordMessage] = useState('')

  useEffect(() => {
    if (isAuthenticated) {
      loadDocuments()
    }
  }, [isAuthenticated])

  const handleLogin = async (username, password) => {
    try {
      const response = await axios.post(`${API_BASE}/admin/login`, {
        username,
        password
      })
      
      setToken(response.data.token)
      setIsAuthenticated(true)
      setLoginError('')
    } catch (error) {
      setLoginError(error.response?.data?.detail || 'Login failed')
    }
  }

  const handleLogout = () => {
    setToken(null)
    setIsAuthenticated(false)
  }

  const loadDocuments = async () => {
    try {
      const response = await axios.get(`${API_BASE}/sources`)
      if (Array.isArray(response.data)) {
        setDocuments(response.data)
      }
    } catch (error) {
      console.error('Failed to load documents:', error)
    }
  }

  const handleFileUpload = async (e) => {
    const file = e.target.files[0]
    if (!file) return

    const formData = new FormData()
    formData.append('file', file)

    setIsUploading(true)
    setUploadStatus('Uploading...')

    try {
      const response = await axios.post(`${API_BASE}/admin/upload`, formData, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'multipart/form-data'
        }
      })
      
      setUploadStatus(`Success! Processed ${response.data.chunks_processed} chunks from ${response.data.filename}`)
      loadDocuments()
      e.target.value = ''
    } catch (error) {
      setUploadStatus(error.response?.data?.detail || 'Upload failed')
    } finally {
      setIsUploading(false)
    }
  }

  const handleChangePassword = async (e) => {
    e.preventDefault()
    
    if (newPassword !== confirmPassword) {
      setPasswordMessage('New passwords do not match')
      return
    }

    if (newPassword.length < 8) {
      setPasswordMessage('Password must be at least 8 characters long')
      return
    }

    try {
      await axios.post(
        `${API_BASE}/admin/change-password`,
        {
          current_password: currentPassword,
          new_password: newPassword
        },
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      )
      
      setPasswordMessage('Password changed successfully!')
      setCurrentPassword('')
      setNewPassword('')
      setConfirmPassword('')
    } catch (error) {
      setPasswordMessage(error.response?.data?.detail || 'Password change failed')
    }
  }

  if (!isAuthenticated) {
    return (
      <div className="admin-page">
        <div className="admin-header">
          <h1>Admin Panel</h1>
          <Link to="/" className="back-link">← Back to Chat</Link>
        </div>
        <LoginForm onLogin={handleLogin} error={loginError} />
      </div>
    )
  }

  return (
    <div className="admin-page">
      <div className="admin-header">
        <h1>Admin Panel</h1>
        <div className="header-actions">
          <Link to="/" className="back-link">← Back to Chat</Link>
          <button onClick={handleLogout} className="logout-button">Logout</button>
        </div>
      </div>

      <div className="admin-content">
        <section className="admin-section">
          <h2>Upload Documents</h2>
          <p className="section-description">
            Upload PDF, DOCX, or TXT maintenance manuals to enhance the knowledge base.
          </p>
          <div className="upload-area">
            <input
              type="file"
              accept=".pdf,.docx,.txt"
              onChange={handleFileUpload}
              disabled={isUploading}
              id="file-upload"
            />
            <label htmlFor="file-upload" className="upload-button">
              {isUploading ? 'Uploading...' : 'Choose File'}
            </label>
          </div>
          {uploadStatus && (
            <div className={`upload-status ${uploadStatus.includes('Success') ? 'success' : 'error'}`}>
              {uploadStatus}
            </div>
          )}
        </section>

        <section className="admin-section">
          <h2>Uploaded Documents</h2>
          <div className="documents-list">
            {Array.isArray(documents) && documents.length > 0 ? (
              <table className="documents-table">
                <thead>
                  <tr>
                    <th>Filename</th>
                    <th>Uploaded</th>
                    <th>Status</th>
                    <th>Chunks</th>
                  </tr>
                </thead>
                <tbody>
                  {documents.map((doc) => (
                    <tr key={doc.id}>
                      <td>{doc.filename}</td>
                      <td>{new Date(doc.uploaded_at).toLocaleDateString()}</td>
                      <td>
                        <span className={`status-badge ${doc.status}`}>
                          {doc.status}
                        </span>
                      </td>
                      <td>{doc.chunks_count || 0}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <div className="empty-state">No documents uploaded yet</div>
            )}
          </div>
        </section>

        <section className="admin-section">
          <h2>Change Password</h2>
          <form onSubmit={handleChangePassword} className="password-form">
            <div className="form-group">
              <label htmlFor="current-password">Current Password</label>
              <input
                type="password"
                id="current-password"
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                required
              />
            </div>
            <div className="form-group">
              <label htmlFor="new-password">New Password</label>
              <input
                type="password"
                id="new-password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                required
                minLength={8}
              />
            </div>
            <div className="form-group">
              <label htmlFor="confirm-password">Confirm New Password</label>
              <input
                type="password"
                id="confirm-password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
              />
            </div>
            <button type="submit">Change Password</button>
            {passwordMessage && (
              <div className={`message ${passwordMessage.includes('successfully') ? 'success' : 'error'}`}>
                {passwordMessage}
              </div>
            )}
          </form>
        </section>
      </div>
    </div>
  )
}

export default AdminPage
