import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { githubCallback } from '../api/auth'
import { ApiError } from '../api/client'
import { useAuth } from '../store/auth'

function ErrorCard({ message }: { message: string }) {
  return (
    <div className="auth-page">
      <div className="auth-card">
        <h1 className="auth-title scanline">Static</h1>
        <p className="auth-subtitle">GitHub authentication failed</p>
        <p className="error-msg" style={{ textAlign: 'center', marginBottom: 16 }}>{message}</p>
        <p className="auth-link">
          <Link to="/login">Back to login</Link>
        </p>
      </div>
    </div>
  )
}

export default function GitHubCallbackPage() {
  const { setToken } = useAuth()
  const navigate = useNavigate()
  const [error, setError] = useState<string | null>(null)

  const params = new URLSearchParams(window.location.search)
  const code  = params.get('code')
  const state = params.get('state')

  useEffect(() => {
    if (!code || !state) return

    githubCallback({ code, state })
      .then(({ access_token }) => {
        setToken(access_token)
        const pending = sessionStorage.getItem('pendingCipherKey')
        if (pending) {
          sessionStorage.removeItem('pendingCipherKey')
          navigate(`/invite?token=${encodeURIComponent(pending)}`, { replace: true })
        } else {
          navigate('/lobby', { replace: true })
        }
      })
      .catch(err => {
        setError(err instanceof ApiError ? err.message : 'Authentication failed. Please try again.')
      })
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  if (!code || !state) {
    return <ErrorCard message="Invalid callback — missing code or state." />
  }

  if (error) {
    return <ErrorCard message={error} />
  }

  return (
    <div className="center-page">
      <div className="spinner" />
      <span>Authenticating…</span>
    </div>
  )
}
