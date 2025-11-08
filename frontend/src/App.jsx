import React, { Suspense, lazy } from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import ErrorBoundary from './components/ErrorBoundary'
import ChatPage from './pages/ChatPage'

const AdminPage = lazy(() => import('./pages/AdminPage'))

function App() {
  return (
    <ErrorBoundary>
      <Router>
        <Suspense fallback={
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            minHeight: '100vh',
            background: '#1a1a1a',
            color: '#fff'
          }}>
            Loading...
          </div>
        }>
          <Routes>
            <Route path="/" element={<ChatPage />} />
            <Route path="/admin" element={<AdminPage />} />
          </Routes>
        </Suspense>
      </Router>
    </ErrorBoundary>
  )
}

export default App
